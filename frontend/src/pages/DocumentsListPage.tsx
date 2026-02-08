import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import type { AuthUser, DocumentRecord } from "../types";

type DocumentsListPageProps = {
  user: AuthUser;
};

export function DocumentsListPage({ user }: DocumentsListPageProps) {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [title, setTitle] = useState("Untitled document");
  const [error, setError] = useState<string | null>(null);

  async function loadDocuments() {
    try {
      const response = await api.get<DocumentRecord[]>("/docs/");
      setDocuments(response.data);
      setError(null);
    } catch {
      setError("Failed to load documents");
    }
  }

  useEffect(() => {
    void loadDocuments();
  }, []);

  async function createDocument(event: FormEvent) {
    event.preventDefault();
    await api.post<DocumentRecord>("/docs/", { title });
    setTitle("Untitled document");
    await loadDocuments();
  }

  async function renameDocument(documentId: string, nextTitle: string) {
    await api.patch<DocumentRecord>(`/docs/${documentId}/`, { title: nextTitle });
    await loadDocuments();
  }

  async function archiveDocument(documentId: string) {
    await api.post(`/docs/${documentId}/archive/`);
    await loadDocuments();
  }

  async function restoreDocument(documentId: string) {
    await api.post(`/docs/${documentId}/restore/`);
    await loadDocuments();
  }

  return (
    <div className="layout">
      <header className="toolbar">
        <h1>Documents</h1>
        <p>Signed in as {user.username}</p>
      </header>
      <form className="panel create-doc" onSubmit={createDocument}>
        <input value={title} onChange={(event) => setTitle(event.target.value)} />
        <button type="submit">Create</button>
      </form>
      {error ? <p className="error">{error}</p> : null}
      <div className="panel">
        <table>
          <thead>
            <tr>
              <th>Title</th>
              <th>Role</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((document) => (
              <tr key={document.id}>
                <td>
                  <Link to={`/docs/${document.id}`}>{document.title}</Link>
                </td>
                <td>{document.my_role}</td>
                <td>{document.is_archived ? "Archived" : "Active"}</td>
                <td className="actions">
                  <button
                    onClick={() => {
                      const nextTitle = window.prompt("Rename document", document.title);
                      if (nextTitle && nextTitle !== document.title) {
                        void renameDocument(document.id, nextTitle);
                      }
                    }}
                  >
                    Rename
                  </button>
                  {document.is_archived ? (
                    <button onClick={() => void restoreDocument(document.id)}>Restore</button>
                  ) : (
                    <button onClick={() => void archiveDocument(document.id)}>Archive</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
