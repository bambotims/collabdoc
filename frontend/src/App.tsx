import { Navigate, Route, Routes } from "react-router-dom";
import { useEffect, useState } from "react";

import { api } from "./api/client";
import type { AuthUser } from "./types";
import { DocumentEditorPage } from "./pages/DocumentEditorPage";
import { DocumentsListPage } from "./pages/DocumentsListPage";
import { LoginPage } from "./pages/LoginPage";

function App() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<AuthUser>("/auth/me")
      .then((response) => setUser(response.data))
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="screen-center">Loading...</div>;
  }

  if (!user) {
    return <LoginPage onLogin={setUser} />;
  }

  return (
    <Routes>
      <Route path="/docs" element={<DocumentsListPage user={user} />} />
      <Route path="/docs/:docId" element={<DocumentEditorPage user={user} />} />
      <Route path="*" element={<Navigate to="/docs" replace />} />
    </Routes>
  );
}

export default App;
