import React, { useEffect, useState } from "react";
import api, { getToken, setToken } from "./api";
import AuthForm from "./AuthForm";
import ResumeUpload from "./ResumeUpload";

function App() {
  // undefined = still checking a stored token, null = signed out.
  const [username, setUsername] = useState(() => (getToken() ? undefined : null));

  useEffect(() => {
    if (!getToken()) return;

    // A stored token may have been revoked since last visit; ask before trusting it.
    api
      .get("/api/auth/me/")
      .then(({ data }) => setUsername(data.username))
      .catch(() => setUsername(null));
  }, []);

  useEffect(() => {
    const signOut = () => setUsername(null);
    window.addEventListener("auth:expired", signOut);
    return () => window.removeEventListener("auth:expired", signOut);
  }, []);

  if (username === undefined) {
    return (
      <div className="flex min-h-screen items-center justify-center" role="status">
        <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-muted">
          Checking your session…
        </p>
      </div>
    );
  }

  if (username === null) return <AuthForm onAuthenticated={setUsername} />;

  return (
    <ResumeUpload
      username={username}
      onSignOut={() => {
        setToken(null);
        setUsername(null);
      }}
    />
  );
}

export default App;
