from __future__ import annotations

import re
from typing import Any

from ..services.sandbox import read_file, write_file


def assembleBackendEntry(project_id: str, fileRegistry: list[dict[str, Any]], blueprint: dict[str, Any]) -> None:
    route_files = [
        entry for entry in fileRegistry
        if "backend/src/routes/" in str(entry.get("path", "")) and str(entry.get("path", "")).endswith(".js")
    ]
    if not route_files:
        return

    content = _read_or_empty(project_id, "backend/src/index.js")
    if "ROUTE_IMPORTS_PLACEHOLDER" not in content and "ROUTE_MOUNTS_PLACEHOLDER" not in content:
        missing_routes = [
            route for route in route_files
            if route["path"].rsplit("/", 1)[-1].removesuffix(".js") not in content
        ]
        if not missing_routes:
            return

    imports = []
    mounts = []
    for route_file in route_files:
        file_name = route_file["path"].rsplit("/", 1)[-1].removesuffix(".js")
        var_name = re.sub(r"[^a-zA-Z]", "", re.sub(r"Routes?$", "", file_name)) + "Routes"
        mount_path = _mount_path_for_route(file_name, blueprint)
        imports.append(f"import {var_name} from './routes/{file_name}.js';")
        mounts.append(f"app.use('{mount_path}', {var_name});")

    if "ROUTE_IMPORTS_PLACEHOLDER" in content:
        content = content.replace("// ROUTE_IMPORTS_PLACEHOLDER", "\n".join(imports))
        content = content.replace("// ROUTE_MOUNTS_PLACEHOLDER", "\n".join(mounts))
    else:
        content = f"""import express from 'express';
import cors from 'cors';
import 'dotenv/config';
import {{ connectDB }} from './config/db.js';
{chr(10).join(imports)}

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

app.get('/api/health', (_req, res) => {{
  res.json({{ status: 'ok', timestamp: new Date().toISOString() }});
}});

{chr(10).join(mounts)}

app.use((err, _req, res, _next) => {{
  console.error(err.stack);
  res.status(500).json({{ success: false, message: err.message || 'Internal server error' }});
}});

connectDB().then(() => {{
  app.listen(PORT, () => console.log(`Server running on port ${{PORT}}`));
}});

export default app;
"""
    write_file(project_id, "backend/src/index.js", content)


def assembleFrontendEntry(project_id: str, fileRegistry: list[dict[str, Any]], blueprint: dict[str, Any]) -> None:
    page_files = [
        entry for entry in fileRegistry
        if "frontend/src/pages/" in str(entry.get("path", "")) and str(entry.get("path", "")).endswith(".jsx")
    ]
    if not page_files:
        return

    content = _read_or_empty(project_id, "frontend/src/App.jsx")
    if "PAGE_IMPORTS_PLACEHOLDER" not in content and "PAGE_ROUTES_PLACEHOLDER" not in content:
        missing_pages = [
            page for page in page_files
            if page["path"].rsplit("/", 1)[-1].removesuffix(".jsx") not in content
        ]
        if not missing_pages:
            return

    imports = []
    routes = []
    for page_file in page_files:
        component_name = page_file["path"].rsplit("/", 1)[-1].removesuffix(".jsx")
        route = _route_for_page(component_name, blueprint)
        imports.append(f"import {component_name} from './pages/{component_name}';")
        routes.append(f'        <Route path="{route}" element={{<{component_name} />}} />')

    has_auth_context = any("context/Auth" in str(entry.get("path", "")) for entry in fileRegistry)
    auth_import = "import { AuthProvider } from './context/AuthContext';\n" if has_auth_context else ""
    auth_wrap_start = "    <AuthProvider>\n" if has_auth_context else ""
    auth_wrap_end = "    </AuthProvider>\n" if has_auth_context else ""
    has_login = any('"/login"' in route for route in routes)
    has_dashboard = any('"/dashboard"' in route for route in routes)
    default_route = "/dashboard" if has_dashboard else "/login" if has_login else "/"

    content = f"""import {{ BrowserRouter, Routes, Route, Navigate }} from 'react-router-dom';
{auth_import}{chr(10).join(imports)}

export default function App() {{
  return (
    <BrowserRouter>
{auth_wrap_start}      <Routes>
{chr(10).join(routes)}
        <Route path="/" element={{<Navigate to="{default_route}" replace />}} />
      </Routes>
{auth_wrap_end}    </BrowserRouter>
  );
}}
"""
    write_file(project_id, "frontend/src/App.jsx", content)


def _read_or_empty(project_id: str, path: str) -> str:
    try:
        return read_file(project_id, path)
    except Exception:
        return ""


def _mount_path_for_route(file_name: str, blueprint: dict[str, Any]) -> str:
    base = re.sub(r"Routes?$", "", file_name)
    mount_path = "/api/" + re.sub(r"([A-Z])", r"-\1", base).lower().strip("-")
    for entity in blueprint.get("entities", []):
        file_base = file_name.lower().replace("routes", "").replace("route", "")
        if file_base in str(entity.get("modelFile", "")).lower() or file_base in str(entity.get("routeFile", "")).lower():
            return entity.get("apiPath") or mount_path
    if "auth" in file_name.lower():
        return "/api/auth"
    return mount_path


def _route_for_page(component_name: str, blueprint: dict[str, Any]) -> str:
    route = "/" + component_name.replace("Page", "").lower()
    for page in blueprint.get("frontendPages", []):
        if page.get("name") in {component_name, component_name.replace("Page", "")}:
            return page.get("route") or route
    lower = component_name.lower()
    if "login" in lower:
        return "/login"
    if "register" in lower:
        return "/register"
    if "dashboard" in lower:
        return "/dashboard"
    return route
