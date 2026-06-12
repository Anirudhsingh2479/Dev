import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { createProjectZipBuffer } from "../../gateway/src/services/projectZip.js";

function findNames(buffer) {
  const names = [];
  let offset = 0;
  while (offset < buffer.length - 46) {
    if (buffer.readUInt32LE(offset) !== 0x02014b50) {
      offset += 1;
      continue;
    }

    const nameLength = buffer.readUInt16LE(offset + 28);
    const extraLength = buffer.readUInt16LE(offset + 30);
    const commentLength = buffer.readUInt16LE(offset + 32);
    const nameStart = offset + 46;
    names.push(buffer.subarray(nameStart, nameStart + nameLength).toString("utf8"));
    offset = nameStart + nameLength + extraLength + commentLength;
  }
  return names;
}

async function writeFile(filePath, content) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, content);
}

async function run() {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "aidev-zip-test-"));
  const sandboxId = "sandbox-123456";
  const sandboxPath = path.join(root, sandboxId);

  await writeFile(path.join(sandboxPath, "backend", "package.json"), '{"name":"backend"}\n');
  await writeFile(path.join(sandboxPath, "backend", "src", "index.js"), "console.log('ok');\n");
  await writeFile(path.join(sandboxPath, "frontend", "src", "App.jsx"), "export default function App() { return null; }\n");
  await writeFile(path.join(sandboxPath, "README.md"), "# Test app\n");

  await writeFile(path.join(sandboxPath, ".env"), "SECRET=hidden\n");
  await writeFile(path.join(sandboxPath, "backend", ".env"), "DATABASE_URL=hidden\n");
  await writeFile(path.join(sandboxPath, ".git", "config"), "hidden\n");
  await writeFile(path.join(sandboxPath, "backend", "node_modules", "express", "package.json"), "{}\n");
  await writeFile(path.join(sandboxPath, "frontend", "dist", "index.html"), "<html></html>\n");
  await writeFile(path.join(sandboxPath, "backend", "server.log"), "hidden\n");

  const oldRoot = process.env.SANDBOX_ROOT;
  process.env.SANDBOX_ROOT = root;

  try {
    const buffer = await createProjectZipBuffer(sandboxId);
    assert.ok(buffer.length > 0, "zip buffer should be non-empty");
    assert.equal(buffer.readUInt32LE(0), 0x04034b50, "zip should start with local file header");

    const names = findNames(buffer);
    assert.ok(names.some((name) => name.includes(`${sandboxId}/backend/src/index.js`)), "backend source included");
    assert.ok(names.some((name) => name.includes(`${sandboxId}/frontend/src/App.jsx`)), "frontend source included");
    assert.ok(names.some((name) => name.includes(`${sandboxId}/README.md`)), "README included");

    assert.ok(!names.some((name) => name.includes("node_modules")), "node_modules excluded");
    assert.ok(!names.some((name) => name.includes("/.git/")), ".git excluded");
    assert.ok(!names.some((name) => name.endsWith("/.env")), ".env excluded");
    assert.ok(!names.some((name) => name.includes("/dist/")), "dist excluded");
    assert.ok(!names.some((name) => name.endsWith(".log")), "logs excluded");

    await assert.rejects(() => createProjectZipBuffer("../bad"), /invalid sandbox id/);
    await assert.rejects(() => createProjectZipBuffer("sandbox-999999"), /sandbox folder not found/);

    console.log("PASS project zip creates safe downloadable archive");
  } finally {
    if (oldRoot === undefined) {
      delete process.env.SANDBOX_ROOT;
    } else {
      process.env.SANDBOX_ROOT = oldRoot;
    }
    await fs.rm(root, { recursive: true, force: true });
  }
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
