const orchestratorUrl = process.env.ORCHESTRATOR_URL || "http://localhost:8000";

async function readError(response) {
  const text = await response.text();
  try {
    return JSON.stringify(JSON.parse(text));
  } catch {
    return text || response.statusText;
  }
}

export async function getOrchestratorHealth() {
  const response = await fetch(`${orchestratorUrl}/health`);
  if (!response.ok) {
    throw new Error(`Orchestrator health failed: ${response.status} ${await readError(response)}`);
  }
  return response.json();
}

export async function createProjectRun(payload) {
  const response = await fetch(`${orchestratorUrl}/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Orchestrator create failed: ${response.status} ${await readError(response)}`);
  }

  return response.json();
}

export async function streamProjectEvents(projectId, onEvent, options = {}) {
  const response = await fetch(`${orchestratorUrl}/runs/${projectId}/events`, {
    signal: options.signal,
  });
  if (!response.ok || !response.body) {
    throw new Error(`Orchestrator stream failed: ${response.status} ${await readError(response)}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() || "";
    for (const chunk of chunks) {
      const line = chunk.split("\n").find((entry) => entry.startsWith("data: "));
      if (line) {
        const event = JSON.parse(line.slice(6));
        await onEvent(event);
      }
    }
  }
}

export async function cancelProjectRun(projectId) {
  const response = await fetch(`${orchestratorUrl}/runs/${projectId}/cancel`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(`Orchestrator cancel failed: ${response.status} ${await readError(response)}`);
  }
  return response.json();
}

export async function stopProjectPreview(projectId, sandboxId) {
  const response = await fetch(`${orchestratorUrl}/runs/${projectId}/preview/stop`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sandbox_id: sandboxId }),
  });
  if (!response.ok) {
    throw new Error(`Orchestrator preview stop failed: ${response.status} ${await readError(response)}`);
  }
  return response.json();
}

export async function restartProjectPreview(projectId, sandboxId, options = {}) {
  const response = await fetch(`${orchestratorUrl}/runs/${projectId}/preview/restart`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sandbox_id: sandboxId,
      user_id: options.userId,
      backend_port: options.backendPort,
      frontend_port: options.frontendPort,
    }),
  });
  if (!response.ok) {
    throw new Error(`Orchestrator preview restart failed: ${response.status} ${await readError(response)}`);
  }
  return response.json();
}

export async function submitProjectInput(projectId, payload) {
  const response = await fetch(`${orchestratorUrl}/runs/${projectId}/input`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Orchestrator input failed: ${response.status} ${await readError(response)}`);
  }

  return response.json();
}

export { orchestratorUrl };
