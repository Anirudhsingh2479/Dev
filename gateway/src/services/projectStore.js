import pg from "pg";

const { Pool } = pg;
const pool = process.env.DATABASE_URL ? new Pool({ connectionString: process.env.DATABASE_URL }) : null;
const memoryProjects = new Map();
const memoryUsers = new Map();

async function ensureProjectsTable() {
  if (!pool) return;
  await pool.query(`
    create table if not exists projects (
      project_id text primary key,
      user_id text not null,
      requirement text not null,
      status text not null,
      last_event_type text,
      last_event_node text,
      last_message text,
      last_state jsonb,
      sandbox_id text,
      preview_frontend_port integer,
      preview_backend_port integer,
      preview_frontend_url text,
      preview_backend_url text,
      preview_running boolean default false,
      created_at timestamptz default now(),
      updated_at timestamptz default now()
    )
  `);
  await pool.query("alter table projects add column if not exists last_state jsonb");
  await pool.query("alter table projects add column if not exists sandbox_id text");
  await pool.query("alter table projects add column if not exists preview_frontend_port integer");
  await pool.query("alter table projects add column if not exists preview_backend_port integer");
  await pool.query("alter table projects add column if not exists preview_frontend_url text");
  await pool.query("alter table projects add column if not exists preview_backend_url text");
  await pool.query("alter table projects add column if not exists preview_running boolean default false");
}

async function ensureUsersTable() {
  if (!pool) return;
  await pool.query(`
    create table if not exists users (
      user_id text primary key,
      email text not null unique,
      display_name text,
      created_at timestamptz default now(),
      updated_at timestamptz default now()
    )
  `);
}

function normalizeProject(project) {
  const lastState = project.last_state || null;
  const sandboxId = project.sandbox_id || lastState?.sandboxId || lastState?.sandbox_id || null;
  const previewFrontendPort = project.preview_frontend_port || lastState?.previewFrontendPort || null;
  const previewBackendPort = project.preview_backend_port || lastState?.previewBackendPort || null;
  const previewFrontendUrl = project.preview_frontend_url || lastState?.previewFrontendUrl || (previewFrontendPort ? `http://localhost:${previewFrontendPort}` : null);
  const previewBackendUrl = project.preview_backend_url || lastState?.previewBackendUrl || (previewBackendPort ? `http://localhost:${previewBackendPort}` : null);
  return {
    project_id: project.project_id,
    user_id: project.user_id || "unknown-user",
    requirement: project.requirement || "",
    status: project.status || "running",
    last_event_type: project.last_event_type || null,
    last_event_node: project.last_event_node || null,
    last_message: project.last_message || null,
    last_state: lastState,
    sandbox_id: sandboxId,
    preview_frontend_port: previewFrontendPort,
    preview_backend_port: previewBackendPort,
    preview_frontend_url: previewFrontendUrl,
    preview_backend_url: previewBackendUrl,
    preview_running: Boolean(project.preview_running),
    created_at: project.created_at || new Date().toISOString(),
    updated_at: project.updated_at || new Date().toISOString(),
  };
}

export async function saveProjectMetadata(project) {
  const normalized = normalizeProject(project);
  memoryProjects.set(normalized.project_id, normalized);

  await ensureProjectsTable();
  if (!pool) return normalized;
  await pool.query(
    `insert into projects (
       project_id, user_id, requirement, status, last_event_type, last_event_node, last_message, last_state,
       sandbox_id, preview_frontend_port, preview_backend_port, preview_frontend_url, preview_backend_url, preview_running
     )
     values ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
     on conflict (project_id) do update set
       status = excluded.status,
       last_event_type = excluded.last_event_type,
       last_event_node = excluded.last_event_node,
       last_message = excluded.last_message,
       last_state = excluded.last_state,
       sandbox_id = excluded.sandbox_id,
       preview_frontend_port = excluded.preview_frontend_port,
       preview_backend_port = excluded.preview_backend_port,
       preview_frontend_url = excluded.preview_frontend_url,
       preview_backend_url = excluded.preview_backend_url,
       preview_running = excluded.preview_running,
       updated_at = now()`,
    [
      normalized.project_id,
      normalized.user_id,
      normalized.requirement,
      normalized.status,
      normalized.last_event_type,
      normalized.last_event_node,
      normalized.last_message,
      normalized.last_state,
      normalized.sandbox_id,
      normalized.preview_frontend_port,
      normalized.preview_backend_port,
      normalized.preview_frontend_url,
      normalized.preview_backend_url,
      normalized.preview_running,
    ],
  );
  return normalized;
}

export async function listProjects(userId = "unknown-user") {
  await ensureProjectsTable();
  if (!pool) {
    return [...memoryProjects.values()]
      .filter((project) => project.user_id === userId)
      .sort((a, b) => String(b.updated_at).localeCompare(String(a.updated_at)));
  }

  const result = await pool.query(
    `select project_id, user_id, requirement, status, last_event_type, last_event_node,
            last_message, last_state, sandbox_id, preview_frontend_port, preview_backend_port,
            preview_frontend_url, preview_backend_url, preview_running, created_at, updated_at
       from projects
      where user_id = $1
      order by updated_at desc`,
    [userId],
  );
  return result.rows;
}

export async function getProjectMetadata(projectId) {
  if (memoryProjects.has(projectId)) return memoryProjects.get(projectId);

  await ensureProjectsTable();
  if (!pool) return null;

  const result = await pool.query(
    `select project_id, user_id, requirement, status, last_event_type, last_event_node,
            last_message, last_state, sandbox_id, preview_frontend_port, preview_backend_port,
            preview_frontend_url, preview_backend_url, preview_running, created_at, updated_at
       from projects
      where project_id = $1`,
    [projectId],
  );
  return result.rows[0] || null;
}

export async function updateProjectFromEvent(projectId, event) {
  const existing = await getProjectMetadata(projectId);
  if (!existing) return null;
  const state = event.state || existing.last_state || null;
  const sandboxId = state?.sandboxId || state?.sandbox_id || existing.sandbox_id || null;
  const previewFrontendPort = state?.previewFrontendPort || existing.preview_frontend_port || null;
  const previewBackendPort = state?.previewBackendPort || existing.preview_backend_port || null;
  const previewFrontendUrl = state?.previewFrontendUrl || existing.preview_frontend_url || (previewFrontendPort ? `http://localhost:${previewFrontendPort}` : null);
  const previewBackendUrl = state?.previewBackendUrl || existing.preview_backend_url || (previewBackendPort ? `http://localhost:${previewBackendPort}` : null);

  const status = event.type === "run.completed"
    ? "completed"
    : event.type === "run.failed"
      ? "failed"
      : event.type === "run.cancelled"
        ? "cancelled"
        : existing.status;

  return saveProjectMetadata({
    ...existing,
    status,
    last_event_type: event.type,
    last_event_node: event.node || null,
    last_message: event.message || "",
    last_state: state,
    sandbox_id: sandboxId,
    preview_frontend_port: previewFrontendPort,
    preview_backend_port: previewBackendPort,
    preview_frontend_url: previewFrontendUrl,
    preview_backend_url: previewBackendUrl,
    preview_running: event.type === "run.completed"
      ? true
      : event.type === "run.failed" || event.type === "run.cancelled"
        ? false
        : Boolean(existing.preview_running),
  });
}

export async function clearActivePreviewForUser(userId, exceptProjectId = null) {
  const projects = await listProjects(userId);
  const active = projects.filter((project) => (
    project.preview_running && project.project_id !== exceptProjectId
  ));
  for (const project of active) {
    await saveProjectMetadata({
      ...project,
      preview_running: false,
      last_event_type: "preview.stopped",
      last_event_node: "gateway",
      last_message: "Preview stopped because another project was started for this user",
    });
  }
  return active;
}

export async function saveUser(user) {
  const normalized = {
    user_id: user.user_id || "unknown-user",
    email: user.email || "",
    display_name: user.display_name || "",
    updated_at: new Date().toISOString(),
  };
  memoryUsers.set(normalized.user_id, normalized);

  await ensureUsersTable();
  if (!pool) return normalized;

  await pool.query(
    `insert into users (user_id, email, display_name)
     values ($1, $2, $3)
     on conflict (email) do update set
       user_id = excluded.user_id,
       display_name = excluded.display_name,
       updated_at = now()`,
    [normalized.user_id, normalized.email, normalized.display_name],
  );
  return normalized;
}
