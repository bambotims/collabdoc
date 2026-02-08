import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import { getApiErrorMessage } from "../api/errors";
import { useToast } from "../components/Toast";
import type { AuthUser, DocumentRecord } from "../types";

type DocumentsListPageProps = {
  user: AuthUser;
};

export function DocumentsListPage({ user }: DocumentsListPageProps) {
  const { pushToast } = useToast();
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [title, setTitle] = useState("Untitled document");

  async function loadDocuments() {
    try {
      const response = await api.get<DocumentRecord[]>("/docs/");
      setDocuments(response.data);
    } catch (error) {
      pushToast(getApiErrorMessage(error, "Failed to load documents."), { variant: "error" });
    }
  }

  useEffect(() => {
    void loadDocuments();
  }, [pushToast]);

  async function createDocument(event: FormEvent) {
    event.preventDefault();
    try {
      await api.post<DocumentRecord>("/docs/", { title });
      setTitle("Untitled document");
      pushToast("Document created.", { variant: "success" });
      await loadDocuments();
    } catch (error) {
      pushToast(getApiErrorMessage(error, "Failed to create document."), { variant: "error" });
    }
  }

  async function renameDocument(documentId: string, nextTitle: string) {
    try {
      await api.patch<DocumentRecord>(`/docs/${documentId}/`, { title: nextTitle });
      pushToast("Document renamed.", { variant: "success" });
      await loadDocuments();
    } catch (error) {
      pushToast(getApiErrorMessage(error, "Failed to rename document."), { variant: "error" });
    }
  }

  async function archiveDocument(documentId: string) {
    try {
      await api.post(`/docs/${documentId}/archive/`);
      pushToast("Document archived.", { variant: "success" });
      await loadDocuments();
    } catch (error) {
      pushToast(getApiErrorMessage(error, "Failed to archive document."), { variant: "error" });
    }
  }

  async function restoreDocument(documentId: string) {
    try {
      await api.post(`/docs/${documentId}/restore/`);
      pushToast("Document restored.", { variant: "success" });
      await loadDocuments();
    } catch (error) {
      pushToast(getApiErrorMessage(error, "Failed to restore document."), { variant: "error" });
    }
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
