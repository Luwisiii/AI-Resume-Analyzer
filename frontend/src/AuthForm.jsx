import React, { useState } from "react";
import { FiBriefcase, FiCheck, FiEye, FiEyeOff, FiLock, FiTarget } from "react-icons/fi";
import api, { errorMessage } from "./api";
import { AuthArt } from "./Illustrations";
import Mark from "./Mark";

const PERKS = [
  [FiTarget, "See which skills recruiters' software can actually read from your resume."],
  [FiBriefcase, "Get matched to live job postings, with a direct link to apply."],
  [FiLock, "Your resume is private to your account and never shared."],
];

const AuthForm = ({ onAuthenticated }) => {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [showPassword, setShowPassword] = useState(false);
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
        ? { ...form, username: form.username.trim(), email: form.email.trim() }
        : { username: form.username.trim(), password: form.password };
      const { data } = await api.post(`/api/auth/${mode}/`, payload);
      onAuthenticated(data);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const switchTo = (next) => {
    setMode(next);
    setError("");
    setForm((f) => ({ ...f, password: "" }));
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-[1fr_1.05fr]">
      {/* Form column */}
      <div className="flex flex-col px-5 py-8 sm:px-10">
        <div className="flex items-center gap-2.5 text-ink">
          <Mark />
          <span className="text-[15px] font-semibold tracking-tight">Resume Analyzer</span>
        </div>

        <div className="mx-auto flex w-full max-w-[24rem] flex-1 flex-col justify-center py-10 animate-rise">
          <h1 className="text-[1.9rem] font-bold leading-tight tracking-[-0.02em]">
            {isRegister ? "Create your free account" : "Welcome back"}
          </h1>
          <p className="mt-2 text-[15px] text-muted">
            {isRegister
              ? "Get your resume score and job matches in a couple of minutes."
              : "Sign in to analyze a resume and see your latest matches."}
          </p>

          <form onSubmit={submit} className="mt-8 space-y-5">
            <div>
              <label className="mb-1.5 block text-sm font-medium" htmlFor="username">
                Username
              </label>
              <input
                id="username"
                value={form.username}
                onChange={update("username")}
                autoComplete="username"
                autoCapitalize="none"
                spellCheck={false}
                maxLength={150}
                required
                placeholder="jane.doe"
                className="field"
              />
            </div>

            {isRegister && (
              <div>
                <label className="mb-1.5 block text-sm font-medium" htmlFor="email">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  value={form.email}
                  onChange={update("email")}
                  autoComplete="email"
                  maxLength={254}
                  required
                  placeholder="jane@example.com"
                  className="field"
                />
              </div>
            )}

            <div>
              <label className="mb-1.5 block text-sm font-medium" htmlFor="password">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={form.password}
                  onChange={update("password")}
                  autoComplete={isRegister ? "new-password" : "current-password"}
                  minLength={isRegister ? 8 : undefined}
                  maxLength={128}
                  required
                  aria-describedby={isRegister ? "password-hint" : undefined}
                  className="field pr-11"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-muted hover:text-ink"
                >
                  {showPassword ? <FiEyeOff /> : <FiEye />}
                </button>
              </div>
              {isRegister && (
                <p id="password-hint" className="mt-1.5 text-xs text-muted">
                  At least 8 characters. Avoid common passwords, all-numbers, or your username.
                </p>
              )}
            </div>

            {error && (
              <p role="alert" className="rounded-[10px] border border-low/20 bg-low/5 px-3.5 py-2.5 text-sm text-low">
                {error}
              </p>
            )}

            <button type="submit" disabled={busy} className="btn w-full">
              {busy && (
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-paper/40 border-t-paper" />
              )}
              {busy
                ? isRegister
                  ? "Creating account…"
                  : "Signing in…"
                : isRegister
                ? "Create account"
                : "Sign in"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-muted">
            {isRegister ? "Already have an account? " : "New to Resume Analyzer? "}
            <button
              type="button"
              onClick={() => switchTo(isRegister ? "login" : "register")}
              className="font-semibold text-stamp hover:underline"
            >
              {isRegister ? "Sign in" : "Create an account"}
            </button>
          </p>
        </div>

        <p className="text-center text-xs text-muted">
          © {new Date().getFullYear()} Resume Analyzer · Your data stays in your account.
        </p>
      </div>

      {/* Photo column */}
      <div className="relative hidden overflow-hidden bg-ink lg:block">
        <AuthArt className="absolute inset-0 h-full w-full" />
        <div className="absolute inset-0 bg-gradient-to-t from-ink via-ink/40 to-transparent" />

        <div className="absolute inset-x-0 bottom-0 p-10 text-paper xl:p-14">
          <h2 className="max-w-md text-[1.75rem] font-bold leading-tight tracking-[-0.02em]">
            Know how your resume reads before a recruiter does.
          </h2>
          <ul className="mt-6 max-w-md space-y-3">
            {PERKS.map(([icon, text]) => {
              const Icon = icon;
              return (
              <li key={text} className="flex gap-3 text-[15px] text-paper/85">
                <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-paper/15">
                  <Icon className="h-3.5 w-3.5" />
                </span>
                {text}
              </li>
              );
            })}
          </ul>
          <p className="mt-8 flex items-center gap-2 text-xs text-paper/60">
            <FiCheck /> Free to use · Private by default
          </p>
        </div>
      </div>
    </div>
  );
};

export default AuthForm;
