import { Navigate, Route, Routes } from "react-router-dom";
import { useEffect, useState } from "react";

import { api } from "./api/client";
import { ToastProvider } from "./components/Toast";
import type { AuthUser } from "./types";
import { DocumentEditorPage } from "./pages/DocumentEditorPage";
import { DocumentsListPage } from "./pages/DocumentsListPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";

function App() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/auth/csrf")
      .catch(() => null)
      .finally(() => {
        api
          .get<AuthUser>("/auth/me")
          .then((response) => setUser(response.data))
          .catch(() => setUser(null))
          .finally(() => setLoading(false));
      });
  }, []);

  if (loading) {
    return <div className="screen-center">Loading...</div>;
  }

  if (!user) {
    return (
      <ToastProvider>
        <Routes>
          <Route path="/login" element={<LoginPage onLogin={setUser} />} />
          <Route path="/register" element={<RegisterPage onRegister={setUser} />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </ToastProvider>
    );
  }

  return (
    <ToastProvider>
      <Routes>
        <Route path="/docs" element={<DocumentsListPage user={user} />} />
        <Route path="/docs/:docId" element={<DocumentEditorPage user={user} />} />
        <Route path="*" element={<Navigate to="/docs" replace />} />
      </Routes>
    </ToastProvider>
  );
}

export default App;
