import React, { useState } from "react";
import { Loader2 } from "lucide-react";
import { gatewayJson } from "../api/gateway";

function AuthField({ label, ...props }) {
  return (
    <label className="auth-field">
      <span>{label}</span>
      <input {...props} />
    </label>
  );
}

export default function AuthScreen({ onAuthenticated }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({
    firstName: "",
    lastName: "",
    userName: "",
    emailId: "",
    password: "",
    otp: "",
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const isSignup = mode === "signup";

  function updateField(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  }

  async function sendOtp() {
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const data = await gatewayJson("/api/auth/sendotp", {
        method: "POST",
        body: JSON.stringify({ emailId: form.emailId, userName: form.userName }),
      });
      setMessage(data.message || "OTP sent. Please check your email.");
    } catch (otpError) {
      setError(otpError.message || "Could not send OTP.");
    } finally {
      setLoading(false);
    }
  }

  async function submitAuth(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const endpoint = isSignup ? "/api/auth/register" : "/api/auth/login";
      const payload = isSignup
        ? form
        : {
          emailId: form.emailId.includes("@") ? form.emailId : undefined,
          userName: form.emailId.includes("@") ? undefined : form.emailId,
          password: form.password,
        };
      const data = await gatewayJson(endpoint, { method: "POST", body: JSON.stringify(payload) });
      await onAuthenticated(data.user);
    } catch (authError) {
      setError(authError.message || "Authentication failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <div className="auth-panel">
          <p className="eyebrow">Multi-Agent App Builder</p>
          <h1>AgentForge</h1>
          <p>Sign in before creating projects, opening previews, or managing Docker containers.</p>
          <div className="auth-note">
            <span>Access</span>
            <strong>User accounts only</strong>
          </div>
        </div>

        <form className="auth-form" onSubmit={submitAuth}>
          <div className="auth-tabs">
            {["login", "signup"].map((item) => (
              <button
                className={mode === item ? "active" : ""}
                key={item}
                onClick={() => {
                  setMode(item);
                  setError("");
                  setMessage("");
                }}
                type="button"
              >
                {item}
              </button>
            ))}
          </div>

          <div>
            <h2>{isSignup ? "Create Account" : "Welcome Back"}</h2>
            <p className="muted">
              {isSignup
                ? "Use a strong password with uppercase, lowercase, number, and symbol."
                : "Use your email or username to continue."}
            </p>
          </div>

          {isSignup ? (
            <div className="auth-two">
              <AuthField label="First name" name="firstName" value={form.firstName} onChange={updateField} />
              <AuthField label="Last name" name="lastName" value={form.lastName} onChange={updateField} />
            </div>
          ) : null}

          {isSignup ? <AuthField label="Username" name="userName" value={form.userName} onChange={updateField} /> : null}
          <AuthField label={isSignup ? "Email" : "Email or username"} name="emailId" value={form.emailId} onChange={updateField} />
          <AuthField label="Password" name="password" type="password" value={form.password} onChange={updateField} />

          {isSignup ? (
            <div className="otp-row">
              <AuthField label="OTP" name="otp" value={form.otp} onChange={updateField} />
              <button className="secondary-action" disabled={loading || !form.emailId || !form.userName} onClick={sendOtp} type="button">
                Send OTP
              </button>
            </div>
          ) : null}

          {message ? <p className="auth-message">{message}</p> : null}
          {error ? <p className="auth-error">{error}</p> : null}

          <button className="primary-action auth-submit" disabled={loading} type="submit">
            {loading ? <Loader2 className="spin" size={18} /> : null}
            {loading ? "Please wait..." : isSignup ? "Create Account" : "Login"}
          </button>
        </form>
      </section>
    </main>
  );
}
