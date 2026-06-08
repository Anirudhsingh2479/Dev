import "dotenv/config";
import cookieParser from "cookie-parser";
import cors from "cors";
import express from "express";
import { createServer } from "http";
import { WebSocket, WebSocketServer } from "ws";
import authRouter from "./routes/auth.js";
import projectsRouter from "./routes/projects.js";
import { connectMongo } from "./config/mongo.js";
import { connectRedis } from "./config/redis.js";
import { requireAuth } from "./middleware/auth.js";
import { getOrchestratorHealth, streamProjectEvents } from "./services/orchestratorClient.js";
import { getProjectMetadata, updateProjectFromEvent } from "./services/projectStore.js";

const app = express();
const port = Number(process.env.PORT || 3000);
const frontendUrl = process.env.FRONTEND_URL || "http://localhost:5173";

app.use(cors({ origin: frontendUrl, credentials: true }));
app.use(express.json({ limit: "2mb" }));
app.use(cookieParser());

app.get("/api/health", async (_req, res) => {
  try {
    const orchestrator = await getOrchestratorHealth();
    res.json({
      status: "ok",
      layer: "node-express-gateway",
      orchestrator_url: process.env.ORCHESTRATOR_URL || "http://localhost:8000",
      orchestrator,
    });
  } catch (error) {
    res.status(503).json({
      status: "degraded",
      layer: "node-express-gateway",
      orchestrator_url: process.env.ORCHESTRATOR_URL || "http://localhost:8000",
      error: error.message,
    });
  }
});

app.use("/api/auth", authRouter);
app.use("/api/projects", requireAuth, projectsRouter);

app.use((error, _req, res, _next) => {
  const status = error.status || 500;
  res.status(status).json({ error: error.message || "gateway error" });
});

const server = createServer(app);
const wss = new WebSocketServer({ noServer: true });

server.on("upgrade", async (req, socket, head) => {
  const url = new URL(req.url || "", `http://${req.headers.host}`);
  const match = url.pathname.match(/^\/ws\/projects\/([^/]+)\/events$/);

  if (!match) {
    socket.destroy();
    return;
  }

  const projectId = match[1];
  const project = await getProjectMetadata(projectId);
  if (!project) {
    socket.write("HTTP/1.1 404 Not Found\r\n\r\n");
    socket.destroy();
    return;
  }

  wss.handleUpgrade(req, socket, head, (ws) => {
    wss.emit("connection", ws, req, projectId);
  });
});

wss.on("connection", async (ws, _req, projectId) => {
  const controller = new AbortController();
  ws.on("close", () => controller.abort());

  try {
    await streamProjectEvents(projectId, async (event) => {
      await updateProjectFromEvent(projectId, event);
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(event));
      }
    }, {
      signal: controller.signal,
    });
    ws.close(1000, "stream completed");
  } catch (error) {
    if (controller.signal.aborted || error.name === "AbortError") return;
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "gateway.error", node: "gateway", message: error.message }));
      ws.close(1011, "gateway stream failed");
    }
  }
});

Promise.all([connectMongo(), connectRedis()]).then(() => {
  server.listen(port, () => {
    console.log(`Gateway listening on http://localhost:${port}`);
  });
}).catch((error) => {
  console.error("Gateway startup failed:", error.message);
  process.exit(1);
});
