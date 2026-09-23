import React, { useEffect, useState } from "react";
import api from "./api";
import AuthForm from "./AuthForm";
import ResumeUpload from "./ResumeUpload";

function App() {
  // undefined = still checking the session, null = signed out.
  const [user, setUser] = useState(undefined);

  useEffect(() => {
    // Get the CSRF cookie first; every write after this needs it.
    api
      .get("/api/auth/csrf/")
      .then(() => api.get("/api/auth/me/"))
      .then(({ data }) => setUser(data))
      .catch(() => setUser(null));
  }, []);

  useEffect(() => {
    const signOut = () => setUser(null);
    window.addEventListener("auth:expired", signOut);
    return () => window.removeEventListener("auth:expired", signOut);
  }, []);

  if (user === undefined) {
    return (
      <div className="flex min-h-screen items-center justify-center" role="status">
        <span className="h-8 w-8 animate-spin rounded-full border-2 border-rule border-t-stamp" />
        <span className="sr-only">Checking your session…</span>
      </div>
    );
  }

  if (user === null) return <AuthForm onAuthenticated={setUser} />;

  return (
    <ResumeUpload
      user={user}
      onSignOut={async () => {
        try {
          await api.post("/api/auth/logout/");
        } finally {
          setUser(null);
        }
      }}
    />
  );
}

export default App;
