from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .sandbox_process import _write
from .sandbox_state import SANDBOX_BACKEND_HOST_PORT


def _scaffold(sandbox_path: Path, dependencies: dict[str, Any] | None, db_type: str, db_url: str) -> None:
    backend_path = sandbox_path / "backend"
    frontend_path = sandbox_path / "frontend"
    for folder in ["src", "src/models", "src/routes", "src/middleware", "src/config", "src/utils"]:
        (backend_path / folder).mkdir(parents=True, exist_ok=True)
    for folder in ["src", "src/pages", "src/components", "src/hooks", "src/context", "src/utils"]:
        (frontend_path / folder).mkdir(parents=True, exist_ok=True)

    backend_deps = (dependencies or {}).get("backend", {})
    frontend_deps = (dependencies or {}).get("frontend", {})
    _write(backend_path / "package.json", json.dumps({
        "name": backend_deps.get("name", "backend"),
        "version": "1.0.0",
        "type": "module",
        "main": "src/index.js",
        "scripts": {"start": "node src/index.js", "dev": "nodemon src/index.js"},
        "dependencies": backend_deps.get("dependencies", {}),
        "devDependencies": backend_deps.get("devDependencies", {}),
    }, indent=2) + "\n")
    _write(frontend_path / "package.json", json.dumps({
        "name": frontend_deps.get("name", "frontend"),
        "version": "1.0.0",
        "type": "module",
        "scripts": {"dev": "vite", "build": "vite build", "preview": "vite preview"},
        "dependencies": frontend_deps.get("dependencies", {}),
        "devDependencies": frontend_deps.get("devDependencies", {}),
    }, indent=2) + "\n")
    _write(backend_path / ".env", "\n".join([
        "PORT=5000",
        f"DATABASE_URL={db_url}",
        "JWT_SECRET=dev-secret-change-in-production",
        "NODE_ENV=development",
    ]) + "\n")
    _write(frontend_path / ".env", f"VITE_API_URL=http://localhost:{SANDBOX_BACKEND_HOST_PORT}/api\n")
    _write(sandbox_path / ".gitignore", "node_modules/\n.env\ndist/\n.DS_Store\n*.log\n")

    if db_type == "postgres":
        _write(backend_path / "src/config/db.js", """import pg from 'pg';
import 'dotenv/config';

const pool = new pg.Pool({
  connectionString: process.env.DATABASE_URL,
});

pool.on('error', (err) => {
  console.error('Unexpected DB error:', err);
});

export { pool };

export async function connectDB() {
  try {
    const client = await pool.connect();
    console.log('Connected to PostgreSQL');
    client.release();
  } catch (err) {
    console.error('DB connection failed:', err.message);
  }
}
""")
    else:
        _write(backend_path / "src/config/db.js", """import mongoose from 'mongoose';
import 'dotenv/config';

export async function connectDB() {
  try {
    await mongoose.connect(process.env.DATABASE_URL);
    console.log('Connected to MongoDB');
  } catch (err) {
    console.error('DB connection failed:', err.message);
  }
}

export default mongoose;
""")

    _write(backend_path / "src/index.js", """import express from 'express';
import cors from 'cors';
import 'dotenv/config';
import { connectDB } from './config/db.js';

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// ROUTE_IMPORTS_PLACEHOLDER
// ROUTE_MOUNTS_PLACEHOLDER

app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ success: false, message: err.message || 'Internal server error' });
});

connectDB().then(() => {
  app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
  });
});

export default app;
""")
    _write(backend_path / "src/middleware/auth.js", """import jwt from 'jsonwebtoken';

export function authenticateToken(req, res, next) {
  const authHeader = req.headers.authorization;
  const token = authHeader && authHeader.split(' ')[1];
  if (!token) return res.status(401).json({ success: false, message: 'No token provided' });

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (err) {
    return res.status(403).json({ success: false, message: 'Invalid token' });
  }
}

export function authorizeRole(...roles) {
  return (req, res, next) => {
    if (!req.user || !roles.includes(req.user.role)) {
      return res.status(403).json({ success: false, message: 'Forbidden' });
    }
    next();
  };
}
""")
    _write(frontend_path / "index.html", """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>App</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
""")
    _write(frontend_path / "src/main.jsx", """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
""")
    _write(frontend_path / "src/App.jsx", """import { BrowserRouter, Routes, Route } from 'react-router-dom';

// PAGE_IMPORTS_PLACEHOLDER

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<div className="min-h-screen bg-gray-950 text-gray-100 flex items-center justify-center"><p>Loading...</p></div>} />
        {/* PAGE_ROUTES_PLACEHOLDER */}
      </Routes>
    </BrowserRouter>
  );
}
""")
    _write(frontend_path / "src/index.css", "@tailwind base;\n@tailwind components;\n@tailwind utilities;\n")
    _write(frontend_path / "tailwind.config.js", """/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: { extend: {} },
  plugins: [],
};
""")
    _write(frontend_path / "postcss.config.js", """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
""")
    _write(frontend_path / "vite.config.js", """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': process.env.VITE_API_PROXY_TARGET || 'http://localhost:5000'
    }
  }
});
""")
    _write(frontend_path / "src/utils/api.js", """import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default api;
""")
