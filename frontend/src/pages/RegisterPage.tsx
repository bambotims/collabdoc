import { Link } from "react-router-dom";
import { useState, type FormEvent } from "react";

import { api } from "../api/client";
import { getApiErrorMessage } from "../api/errors";
import { useToast } from "../components/Toast";
import type { AuthUser } from "../types";

type RegisterPageProps = {
  onRegister: (user: AuthUser) => void;
};

export function RegisterPage({ onRegister }: RegisterPageProps) {
  const { pushToast } = useToast();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (submitting) {
      return;
    }
    setSubmitting(true);
    try {
      await api.get("/auth/csrf");
      const response = await api.post<AuthUser>("/auth/register", {
        username,
        email,
        password,
        password_confirm: passwordConfirm,
      });
      pushToast("Account created.", { variant: "success" });
      onRegister(response.data);
    } catch (error) {
      pushToast(getApiErrorMessage(error, "Registration failed."), { variant: "error" });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="screen-center">
      <form className="panel auth" onSubmit={handleSubmit}>
        <h1>Create account</h1>
        <input value={username} onChange={(event) => setUsername(event.target.value)} placeholder="Username" required />
        <input
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="Email"
          required
        />
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Password"
          minLength={8}
          required
        />
        <input
          type="password"
          value={passwordConfirm}
          onChange={(event) => setPasswordConfirm(event.target.value)}
          placeholder="Confirm password"
          minLength={8}
          required
        />
        <button type="submit" disabled={submitting}>
          {submitting ? "Creating..." : "Create account"}
        </button>
        <p className="auth-switch">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </form>
    </div>
  );
}
