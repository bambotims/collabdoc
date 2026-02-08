import { useState, type FormEvent } from "react";

import { api } from "../api/client";
import type { AuthUser } from "../types";

type LoginPageProps = {
  onLogin: (user: AuthUser) => void;
};

export function LoginPage({ onLogin }: LoginPageProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    try {
      const response = await api.post<AuthUser>("/auth/login", { username, password });
      onLogin(response.data);
    } catch {
      setError("Invalid credentials");
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
        {error ? <p className="error">{error}</p> : null}
        <button type="submit">Sign in</button>
      </form>
    </div>
  );
}
