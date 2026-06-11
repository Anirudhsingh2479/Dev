import React from "react";
import {
  AlertCircle,
  CheckCircle2,
  Coins,
  Download,
  ExternalLink,
  FolderTree,
  GitBranch,
  Loader2,
  LogOut,
  MessageSquareText,
  Play,
  RefreshCcw,
  Send,
  Server,
  Square,
  Terminal,
  User,
} from "lucide-react";
import { Metric, Panel } from "./ui";

export default function Dashboard({
  activeProjectId,
  canCancel,
  cancelProject,
  downloadCode,
  error,
  escalationChoice,
  events,
  files,
  hasSandbox,
  health,
  inputAnswer,
  isRunning,
  launchBlocked,
  logout,
  nodes,
  openPreview,
  pendingInput,
  previewFrontendUrl,
  projectId,
  projects,
  projectStatus,
  requirement,
  restartPreview,
  selectedProjectId,
  setEscalationChoice,
  setInputAnswer,
  setProject,
  setRequirement,
  startProject,
  stopPreview,
  submitHumanInput,
  terminalLines,
  tokenSource,
  tokenUsage,
  user,
}) {
  return (
    <main className="shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">Multi-Agent App Builder</p>
          <h1>AgentForge</h1>
        </div>
        <div className={health?.status === "ok" ? "status ok" : "status"}>
          <Server size={16} />
          {health?.status === "ok" ? "Gateway online" : "Gateway checking"}
        </div>
      </section>

      <section className="command-row">
        <div className="identity">
          <User size={16} />
          <span>{user.email || user.emailId}</span>
          <span>{user.userName || user.user_id}</span>
          <button className="logout-button" onClick={logout} type="button">
            <LogOut size={14} />
            Logout
          </button>
        </div>
        <label className="prompt-box">
          <span>Project prompt</span>
          <textarea value={requirement} onChange={(event) => setRequirement(event.target.value)} />
        </label>
        <div className="run-actions">
          <button className="primary-action" onClick={startProject} disabled={launchBlocked || !requirement.trim()}>
            {isRunning ? <Loader2 className="spin" size={18} /> : <Play size={18} />}
            {launchBlocked ? "Project active" : "Launch"}
          </button>
          <button className="danger-action" onClick={() => cancelProject()} disabled={!canCancel} type="button">
            <Square size={16} />
            Cancel Active
          </button>
        </div>
      </section>

      {activeProjectId ? (
        <section className="notice active-run">
          <Loader2 className="spin" size={16} />
          Building {activeProjectId}. Cancel it before launching another project.
        </section>
      ) : null}
      {error ? <section className="notice error"><AlertCircle size={16} /> {error}</section> : null}

      {pendingInput ? (
        <section className="human-input">
          <div className="human-heading">
            <MessageSquareText size={18} />
            <strong>{pendingInput.type === "pm_clarification" ? "PM Clarification" : "Human Escalation"}</strong>
          </div>
          {pendingInput.type === "pm_clarification" ? (
            <ol>
              {(pendingInput.payload?.questions || []).map((question, index) => <li key={`${question}-${index}`}>{question}</li>)}
            </ol>
          ) : (
            <>
              <div className="escalation-options">
                {["guide", "skip", "simplify"].map((choice) => (
                  <button
                    className={escalationChoice === choice ? "choice active" : "choice"}
                    key={choice}
                    onClick={() => setEscalationChoice(choice)}
                    type="button"
                  >
                    {choice}
                  </button>
                ))}
              </div>
              <pre>{pendingInput.payload?.error || "No error details."}</pre>
            </>
          )}
          {pendingInput.type === "pm_clarification" || escalationChoice === "guide" ? (
            <textarea
              value={inputAnswer}
              onChange={(event) => setInputAnswer(event.target.value)}
              placeholder={pendingInput.type === "pm_clarification" ? "Answer the PM questions..." : "Give debugging guidance..."}
            />
          ) : null}
          <button onClick={submitHumanInput} type="button">
            <Send size={18} />
            Send
          </button>
        </section>
      ) : null}

      <section className="summary-row">
        <Metric label="Gateway" value={health?.layer || "checking"} />
        <Metric label="Orchestrator" value={health?.orchestrator?.layer || "via gateway"} />
        <Metric label="Current Project" value={projectId || "none"} />
        <Metric label="Status" value={projectStatus} />
      </section>

      <section className="preview-row">
        <div>
          <span>Preview</span>
          <strong>{projectId ? previewFrontendUrl : "select a project"}</strong>
        </div>
        <button onClick={downloadCode} disabled={!projectId || !hasSandbox} type="button">
          <Download size={16} />
          Download Code
        </button>
        <button onClick={openPreview} disabled={!projectId} type="button">
          <ExternalLink size={16} />
          Open Website
        </button>
        <button onClick={stopPreview} disabled={!projectId || !hasSandbox} type="button">
          <Square size={16} />
          Stop Containers
        </button>
        <button onClick={restartPreview} disabled={!projectId || !hasSandbox || ["running", "queued"].includes(projectStatus)} type="button">
          <RefreshCcw size={16} />
          Restart Containers
        </button>
      </section>

      <section className="pipeline">
        {nodes.map((node) => (
          <div className={events.some((event) => event.node === node) ? "node active" : "node"} key={node}>
            {events.some((event) => event.node === node && event.type === "node.completed") ? <CheckCircle2 size={14} /> : <GitBranch size={14} />}
            <span>{node}</span>
          </div>
        ))}
      </section>

      <section className="grid">
        <Panel title="Projects" icon={<Server size={18} />}>
          <div className="project-list">
            {projects.length ? projects.map((item) => {
              const itemIsActive = ["running", "queued"].includes(item.status);
              return (
                <div className={item.project_id === selectedProjectId ? "project-row active" : "project-row"} key={item.project_id}>
                  <button className="project-select" onClick={() => setProject(item)} type="button">
                    <span>{item.project_id}</span>
                    <small>{item.status}</small>
                  </button>
                  <button
                    className="project-cancel"
                    disabled={!itemIsActive}
                    onClick={() => cancelProject(item.project_id)}
                    title={itemIsActive ? "Cancel this project" : "Only active projects can be cancelled"}
                    type="button"
                  >
                    <Square size={14} />
                  </button>
                </div>
              );
            }) : <p className="muted">No projects yet.</p>}
          </div>
        </Panel>
        <Panel title="File Tree" icon={<FolderTree size={18} />}>
          {files.length ? files.map((file) => <div className="file" key={file}>{file}</div>) : <p className="muted">No sandbox files yet.</p>}
        </Panel>
        <Panel title="Terminal Stream" icon={<Terminal size={18} />}>
          <div className="terminal">
            {terminalLines.length
              ? terminalLines.map((line, index) => <div key={`${line}-${index}`}>{line}</div>)
              : <div className="muted">No terminal output yet.</div>}
          </div>
        </Panel>
        <Panel title="Token And Cost" icon={<Coins size={18} />}>
          <div className="metrics">
            <Metric label="Input" value={tokenUsage.totalInput} />
            <Metric label="Output" value={tokenUsage.totalOutput} />
            <Metric label="Cost" value={`$${Number(tokenUsage.estimatedCost || 0).toFixed(4)}`} />
            <Metric label="Source" value={tokenSource} />
            <Metric label="Calls" value={tokenUsage.calls?.length || 0} />
          </div>
        </Panel>
      </section>
    </main>
  );
}
