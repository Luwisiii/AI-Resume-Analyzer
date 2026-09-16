import React, { useState } from "react";
import api, { setToken } from "./api";
import Mark from "./Mark";

const AuthForm = ({ onAuthenticated }) => {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const isRegister = mode === "register";
  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);

    try {
      const payload = isRegister
        ? form
        : { username: form.username, password: form.password };
      const { data } = await api.post(`/api/auth/${mode}/`, payload);
      setToken(data.token);
      onAuthenticated(form.username);
    } catch (err) {
      const detail = err.response?.data;
      setError(
        // DRF returns {field: [messages]} for validation, {non_field_errors} for
        // a bad login. Show whichever is actually there instead of "failed".
        typeof detail === "object" && detail !== null
          ? Object.values(detail).flat().join(" ")
          : "Something went wrong. Is the API running?"
      );
    } finally {
      setBusy(false);
    }
  };

  const switchTo = (next) => {
    setMode(next);
    setError("");
  };

  const tab = (value, text) => (
    <button
      type="button"
      onClick={() => switchTo(value)}
      aria-pressed={mode === value}
      className={`-mb-px border-b-2 px-1 pb-3 font-mono text-[11px] uppercase tracking-[0.16em] transition-colors ${
        mode === value
          ? "border-ink text-ink"
          : "border-transparent text-muted hover:text-ink"
      }`}
    >
      {text}
    </button>
  );

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-5 py-12">
      <div className="w-full max-w-[26rem] animate-rise">
        <div className="mb-7 flex items-center gap-2.5 text-ink">
          <Mark />
          <span className="text-[15px] font-semibold tracking-tight">Resume Analyzer</span>
        </div>

        <form onSubmit={submit} className="sheet p-7 sm:p-8">
          <div className="mb-7 flex gap-7 border-b border-rule">
            {tab("login", "Sign in")}
            {tab("register", "Create account")}
          </div>

          <label className="label mb-1 block" htmlFor="username">
            Username
          </label>
          <input
            id="username"
            value={form.username}
            onChange={update("username")}
            autoComplete="username"
            required
            className="field mb-6"
          />

          {isRegister && (
            <>
              <label className="label mb-1 block" htmlFor="email">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={form.email}
                onChange={update("email")}
                autoComplete="email"
                className="field mb-6"
              />
            </>
          )}

          <label className="label mb-1 block" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            type="password"
            value={form.password}
            onChange={update("password")}
            autoComplete={isRegister ? "new-password" : "current-password"}
            required
            className="field mb-7"
          />

          {error && (
            <p
              role="alert"
              className="mb-6 border-l-2 border-low bg-low/5 py-2 pl-3 text-sm text-low"
            >
              {error}
            </p>
          )}

          <button type="submit" disabled={busy} className="btn w-full">
            {busy
              ? isRegister
                ? "Creating account…"
                : "Signing in…"
              : isRegister
              ? "Create account"
              : "Sign in"}
          </button>
        </form>

        <p className="mt-5 font-mono text-[11px] leading-relaxed text-muted">
          Your resumes are readable only by your own account.
        </p>
      </div>
    </div>
  );
};

export default AuthForm;
