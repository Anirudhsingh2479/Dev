import React, { useEffect, useMemo, useState } from "react";
import { Loader2 } from "lucide-react";
import { defaultPreviewFrontendUrl, gatewayJson, gatewayUrl, normalizeStreamEvent } from "./api/gateway";
import AuthScreen from "./components/AuthScreen";
import Dashboard from "./components/Dashboard";

export default function App() {
  const [requirement, setRequirement] = useState("Build a todo app with login, categories, and due dates.");
  const [user, setUser] = useState(null);
  const [authChecking, setAuthChecking] = useState(true);
  const [project, setProject] = useState(null);
  const [projects, setProjects] = useState([]);
  const [eventsByProject, setEventsByProject] = useState({});
  const [health, setHealth] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState("");
  const [pendingInput, setPendingInput] = useState(null);
  const [inputAnswer, setInputAnswer] = useState("");
  const [escalationChoice, setEscalationChoice] = useState("guide");

  const projectId = project?.project_id;
  const selectedProject = projects.find((item) => item.project_id === projectId);
  const events = projectId ? eventsByProject[projectId] || [] : [];
  const latestState = useMemo(() => {
    for (let index = events.length - 1; index >= 0; index -= 1) {
      if (events[index]?.state) return events[index].state;
    }
    return project?.last_state || selectedProject?.last_state || null;
  }, [events, project, selectedProject]);

  const files = latestState?.fileTree || [];
  const terminalLines = events.length
    ? events.map((event) => `[${event.node}] ${event.type}: ${event.message}`)
    : latestState?.terminalOutput || [];
  const tokenUsage = latestState?.tokenUsage || { totalInput: 0, totalOutput: 0, estimatedCost: 0 };
  const tokenSource = tokenUsage.calls?.at?.(-1)?.source || "estimate";
  const projectStatus = selectedProject?.status || project?.status || "idle";
  const previewFrontendUrl = selectedProject?.preview_frontend_url
    || project?.preview_frontend_url
    || latestState?.previewFrontendUrl
    || (selectedProject?.preview_frontend_port || project?.preview_frontend_port || latestState?.previewFrontendPort
      ? `http://localhost:${selectedProject?.preview_frontend_port || project?.preview_frontend_port || latestState?.previewFrontendPort}`
      : defaultPreviewFrontendUrl);
  const activeProject = projects.find((item) => ["running", "queued"].includes(item.status));
  const activeProjectId = activeProject?.project_id || "";
  const launchBlocked = Boolean(isRunning || activeProjectId);
  const canCancel = Boolean(activeProjectId || (projectId && ["running", "queued"].includes(projectStatus)));
  const hasSandbox = Boolean(latestState?.sandboxId || project?.last_state?.sandboxId || selectedProject?.last_state?.sandboxId);

  const nodes = useMemo(() => [
    "pmAgent", "architectStep1", "architectStep2", "architectStep3", "architectStep4",
    "architectStep5", "blueprintValidator", "plannerAgent", "setupSandbox",
    "sandboxHealthCheck", "selectNextTask", "contextBuilder", "coderAgent",
    "updateRegistry", "reviewerAgent", "executorAgent", "snapshotManager",
    "debuggerAgent", "simplifyTask", "humanEscalation", "phaseVerification",
    "patternExtractor", "stateCompactor", "deploymentVerifier", "presentToUser",
  ], []);

  useEffect(() => {
    let ignore = false;
    async function boot() {
      try {
        const login = await gatewayJson("/api/auth/check");
        if (ignore) return;
        setUser(login.user);
        gatewayJson("/api/health")
          .then((healthResponse) => !ignore && setHealth(healthResponse))
          .catch((healthError) => !ignore && setHealth({ status: "degraded", layer: "node-express-gateway", error: healthError.message }));
        const list = await gatewayJson("/api/projects");
        if (!ignore) setProjects(list.projects || []);
      } catch (bootError) {
        if (!ignore && !String(bootError.message || "").includes("Unauthenticated")) setError(bootError.message);
      } finally {
        if (!ignore) setAuthChecking(false);
      }
    }
    boot();
    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    if (!projectId || !["running", "queued"].includes(projectStatus)) return undefined;
    const source = new EventSource(`${gatewayUrl}/api/projects/${projectId}/events`, { withCredentials: true });
    source.onmessage = (message) => {
      const event = normalizeStreamEvent(JSON.parse(message.data));
      setEventsByProject((current) => ({ ...current, [projectId]: [...(current[projectId] || []), event] }));
      const patch = {
        last_event_type: event.type,
        last_event_node: event.node,
        last_message: event.message,
        ...(event.state ? { last_state: event.state } : {}),
      };
      setProjects((current) => current.map((item) => (item.project_id === projectId ? { ...item, ...patch } : item)));
      setProject((current) => (current?.project_id === projectId ? { ...current, ...patch } : current));
      if (event.type === "input.requested") {
        setPendingInput(event.state);
        setInputAnswer("");
        setEscalationChoice(event.state?.type === "escalation" ? "guide" : "skip");
      }
      if (event.type === "input.received") {
        setPendingInput(null);
        setInputAnswer("");
      }
      if (["run.completed", "run.failed", "run.cancelled"].includes(event.type)) {
        setProjects((current) => current.map((item) => (
          item.project_id === projectId
            ? { ...item, status: event.type === "run.completed" ? "completed" : event.type === "run.cancelled" ? "cancelled" : "failed", ...patch }
            : item
        )));
        setIsRunning(false);
        source.close();
      }
    };
    source.onerror = () => {
      setIsRunning(false);
      setError("Gateway event stream disconnected.");
      source.close();
    };
    return () => source.close();
  }, [projectId, projectStatus]);

  async function refreshAfterAuth(authUser) {
    setUser(authUser);
    setError("");
    setProject(null);
    setEventsByProject({});
    const [healthResponse, list] = await Promise.all([
      gatewayJson("/api/health").catch((healthError) => ({ status: "degraded", layer: "node-express-gateway", error: healthError.message })),
      gatewayJson("/api/projects"),
    ]);
    setHealth(healthResponse);
    setProjects(list.projects || []);
  }

  async function startProject() {
    if (launchBlocked || !user) return;
    try {
      setError("");
      setIsRunning(true);
      setPendingInput(null);
      setInputAnswer("");
      const data = await gatewayJson("/api/projects", {
        method: "POST",
        body: JSON.stringify({ requirement: requirement.trim(), user_id: user.user_id, token_budget_usd: 2.0 }),
      });
      setProject({ project_id: data.project_id, status: data.status });
      setProjects((current) => [data.project, ...current.filter((item) => item.project_id !== data.project_id)]);
      setEventsByProject((current) => ({ ...current, [data.project_id]: [] }));
    } catch (startError) {
      setIsRunning(false);
      setError(startError.message);
    }
  }

  async function logout() {
    try {
      await gatewayJson("/api/auth/logout", { method: "POST" });
    } finally {
      setUser(null);
      setProjects([]);
      setProject(null);
      setEventsByProject({});
      setPendingInput(null);
      setIsRunning(false);
    }
  }

  async function cancelProject(projectIdToCancel = activeProjectId || projectId) {
    if (!projectIdToCancel) return;
    try {
      setError("");
      const data = await gatewayJson(`/api/projects/${projectIdToCancel}/cancel`, { method: "POST" });
      setIsRunning(false);
      if (projectIdToCancel === projectId) setPendingInput(null);
      setProjects((current) => current.map((item) => (
        item.project_id === projectIdToCancel ? { ...item, ...(data.project || {}), status: "cancelled" } : item
      )));
      setProject((current) => (current?.project_id === projectIdToCancel ? { ...current, status: "cancelled" } : current));
    } catch (cancelError) {
      setError(cancelError.message);
    }
  }

  async function submitHumanInput() {
    if (!projectId || !pendingInput?.type) return;
    try {
      setError("");
      const body = pendingInput.type === "pm_clarification"
        ? { type: "pm_clarification", answers: inputAnswer.trim() }
        : { type: "escalation", choice: escalationChoice, guidance: inputAnswer.trim() };
      const result = await gatewayJson(`/api/projects/${projectId}/input`, { method: "POST", body: JSON.stringify(body) });
      if (!result.accepted) {
        setError(result.message || "No pending input request found.");
        return;
      }
      setPendingInput(null);
      setInputAnswer("");
    } catch (inputError) {
      setError(inputError.message);
    }
  }

  async function stopPreview() {
    if (!projectId) return;
    await updatePreview(`/api/projects/${projectId}/preview/stop`);
  }

  async function restartPreview() {
    if (!projectId) return;
    const data = await updatePreview(`/api/projects/${projectId}/preview/restart`);
    if (!data.started) setError((data.errors || ["Preview restart failed"]).join("; "));
    if (data.started && (data.frontendUrl || data.project?.preview_frontend_url)) {
      window.open(data.frontendUrl || data.project.preview_frontend_url, "_blank", "noopener,noreferrer");
    }
  }

  async function updatePreview(path) {
    try {
      setError("");
      const data = await gatewayJson(path, { method: "POST" });
      setProjects((current) => current.map((item) => (item.project_id === projectId ? { ...item, ...(data.project || {}) } : item)));
      setProject((current) => (current?.project_id === projectId ? { ...current, ...(data.project || {}) } : current));
      return data;
    } catch (previewError) {
      setError(previewError.message);
      return {};
    }
  }

  if (authChecking) {
    return <main className="auth-shell"><div className="auth-card compact"><Loader2 className="spin" size={18} />Checking session...</div></main>;
  }
  if (!user) return <AuthScreen onAuthenticated={refreshAfterAuth} />;

  return (
    <Dashboard
      activeProjectId={activeProjectId}
      canCancel={canCancel}
      cancelProject={cancelProject}
      downloadCode={() => projectId && hasSandbox && window.open(`${gatewayUrl}/api/projects/${projectId}/download`, "_blank", "noopener,noreferrer")}
      error={error}
      escalationChoice={escalationChoice}
      events={events}
      files={files}
      hasSandbox={hasSandbox}
      health={health}
      inputAnswer={inputAnswer}
      isRunning={isRunning}
      launchBlocked={launchBlocked}
      logout={logout}
      nodes={nodes}
      openPreview={() => window.open(previewFrontendUrl, "_blank", "noopener,noreferrer")}
      pendingInput={pendingInput}
      previewFrontendUrl={previewFrontendUrl}
      projectId={projectId}
      projects={projects}
      projectStatus={projectStatus}
      requirement={requirement}
      restartPreview={restartPreview}
      selectedProjectId={projectId}
      setEscalationChoice={setEscalationChoice}
      setInputAnswer={setInputAnswer}
      setProject={setProject}
      setRequirement={setRequirement}
      startProject={startProject}
      stopPreview={stopPreview}
      submitHumanInput={submitHumanInput}
      terminalLines={terminalLines}
      tokenSource={tokenSource}
      tokenUsage={tokenUsage}
      user={user}
    />
  );
}
