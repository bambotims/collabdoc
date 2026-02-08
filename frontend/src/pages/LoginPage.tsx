import { Link } from "react-router-dom";
import { useState, type FormEvent } from "react";

import { api } from "../api/client";
import { getApiErrorMessage } from "../api/errors";
import { useToast } from "../components/Toast";
import type { AuthUser } from "../types";

type LoginPageProps = {
  onLogin: (user: AuthUser) => void;
};

export function LoginPage({ onLogin }: LoginPageProps) {
  const { pushToast } = useToast();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (submitting) {
      return;
    }
    setSubmitting(true);
    try {
      await api.get("/auth/csrf");
      const response = await api.post<AuthUser>("/auth/login", { username, password });
      pushToast("Signed in.", { variant: "success" });
      onLogin(response.data);
    } catch (error) {
      pushToast(getApiErrorMessage(error, "Invalid credentials."), { variant: "error" });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="screen-center">
      <form className="panel auth" onSubmit={handleSubmit}>
        <h1>CollabDoc</h1>
        <input value={username} onChange={(event) => setUsername(event.target.value)} placeholder="Username" />
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Password"
        />
        <button type="submit" disabled={submitting}>
          {submitting ? "Signing in..." : "Sign in"}
        </button>
        <p className="auth-switch">
          Need an account? <Link to="/register">Register</Link>
        </p>
      </form>
    </div>
  );
}
