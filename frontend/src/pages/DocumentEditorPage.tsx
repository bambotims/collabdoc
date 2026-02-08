import { useEffect, useMemo, useRef, useState } from "react";
import { EditorContent, useEditor, type Editor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Collaboration from "@tiptap/extension-collaboration";
import CollaborationCursor from "@tiptap/extension-collaboration-cursor";
import { useNavigate, useParams } from "react-router-dom";
import { WebsocketProvider } from "y-websocket";
import * as Y from "yjs";

import { api } from "../api/client";
import { getApiErrorMessage } from "../api/errors";
import { CommentsPanel } from "../components/CommentsPanel";
import { PresencePanel, type PresenceUser } from "../components/PresencePanel";
import { SnapshotPanel } from "../components/SnapshotPanel";
import { useToast } from "../components/Toast";
import type { AuthUser, CommentThread, SnapshotRecord } from "../types";

type CollabTokenResponse = {
  token: string;
  expires_at: string;
  role: "owner" | "editor" | "commenter" | "viewer";
};

type DocumentEditorPageProps = {
  user: AuthUser;
};

export function DocumentEditorPage({ user }: DocumentEditorPageProps) {
  const { pushToast } = useToast();
  const { docId } = useParams();
  const navigate = useNavigate();
  const [provider, setProvider] = useState<WebsocketProvider | null>(null);
  const [role, setRole] = useState<CollabTokenResponse["role"] | null>(null);
  const [connectionStatus, setConnectionStatus] = useState("disconnected");
  const [saveStatus, setSaveStatus] = useState("syncing");
  const [presenceUsers, setPresenceUsers] = useState<PresenceUser[]>([]);
  const [comments, setComments] = useState<CommentThread[]>([]);
  const [snapshots, setSnapshots] = useState<SnapshotRecord[]>([]);
  const editorRef = useRef<Editor | null>(null);
  const ydocRef = useRef<Y.Doc | null>(null);

  const canEdit = role === "owner" || role === "editor";

  useEffect(() => {
    if (!docId) {
      return;
    }
    const currentDocId: string = docId;

    let unmounted = false;
    const ydoc = new Y.Doc();
    ydocRef.current = ydoc;

    async function bootstrap() {
      try {
        const tokenResponse = await api.post<CollabTokenResponse>(`/docs/${currentDocId}/collab-token`);
        if (unmounted) {
          return;
        }
        setRole(tokenResponse.data.role);
        const wsUrl = buildWsUrl();
        const wsProvider = new WebsocketProvider(`${wsUrl}/ws/docs`, currentDocId, ydoc, {
          params: { token: tokenResponse.data.token },
        });
        wsProvider.awareness.setLocalStateField("user", {
          name: user.username,
          color: colorFromUsername(user.username),
        });
        wsProvider.on("status", (event: { status: string }) => {
          if (!unmounted) {
            setConnectionStatus(event.status);
          }
        });
        wsProvider.on("sync", (isSynced: boolean) => {
          if (!unmounted) {
            setSaveStatus(isSynced ? "saved" : "syncing");
          }
        });
        const handlePresence = () => {
          const users = Array.from(wsProvider.awareness.getStates().entries()).map(([clientId, state]) => {
            const userState = (state as { user?: { name?: string; color?: string } }).user;
            return {
              clientId: String(clientId),
              name: userState?.name ?? `user-${clientId}`,
              color: userState?.color ?? "#4b8ff7",
            };
          });
          if (!unmounted) {
            setPresenceUsers(users);
          }
        };
        wsProvider.awareness.on("change", handlePresence);
        handlePresence();
        setProvider(wsProvider);
      } catch (error) {
        pushToast(getApiErrorMessage(error, "Failed to connect to collaborative session."), { variant: "error" });
        navigate("/docs");
      }
    }

    void bootstrap();

    return () => {
      unmounted = true;
      setProvider(null);
      editorRef.current = null;
      ydocRef.current?.destroy();
    };
  }, [docId, navigate, pushToast, user.username]);

  useEffect(() => {
    if (!docId) {
      return;
    }
    void loadComments(docId, setComments).catch((error) => {
      pushToast(getApiErrorMessage(error, "Failed to load comments."), { variant: "error" });
    });
    void loadSnapshots(docId, setSnapshots).catch((error) => {
      pushToast(getApiErrorMessage(error, "Failed to load snapshots."), { variant: "error" });
    });
  }, [docId, pushToast]);

  async function createComment(body: string) {
    if (!docId || !ydocRef.current || !editorRef.current) {
      return;
    }

    const selection = editorRef.current.state.selection;
    const fragment = ydocRef.current.getXmlFragment("default");
    const startRel = Y.createRelativePositionFromTypeIndex(fragment, Math.max(selection.from, 0));
    const endRel = Y.createRelativePositionFromTypeIndex(fragment, Math.max(selection.to, selection.from));
    const startRelB64 = toBase64(Y.encodeRelativePosition(startRel));
    const endRelB64 = toBase64(Y.encodeRelativePosition(endRel));

    try {
      await api.post(`/docs/${docId}/comments`, {
        body,
        start_rel_b64: startRelB64,
        end_rel_b64: endRelB64,
      });
      pushToast("Comment added.", { variant: "success" });
      await loadComments(docId, setComments);
    } catch (error) {
      pushToast(getApiErrorMessage(error, "Failed to add comment."), { variant: "error" });
    }
  }

  async function resolveComment(threadId: number) {
    if (!docId) {
      return;
    }
    try {
      await api.post(`/docs/${docId}/comments/${threadId}/resolve`);
      pushToast("Comment resolved.", { variant: "success" });
      await loadComments(docId, setComments);
    } catch (error) {
      pushToast(getApiErrorMessage(error, "Failed to resolve comment."), { variant: "error" });
    }
  }

  async function reopenComment(threadId: number) {
    if (!docId) {
      return;
    }
    try {
      await api.post(`/docs/${docId}/comments/${threadId}/reopen`);
      pushToast("Comment reopened.", { variant: "success" });
      await loadComments(docId, setComments);
    } catch (error) {
      pushToast(getApiErrorMessage(error, "Failed to reopen comment."), { variant: "error" });
    }
  }

  async function createSnapshot() {
    if (!docId) {
      return;
    }
    try {
      await api.post(`/docs/${docId}/snapshots`);
      pushToast("Snapshot created.", { variant: "success" });
      await loadSnapshots(docId, setSnapshots);
    } catch (error) {
      pushToast(getApiErrorMessage(error, "Failed to create snapshot."), { variant: "error" });
    }
  }

  async function restoreSnapshot(snapshotId: number) {
    if (!docId) {
      return;
    }
    try {
      await api.post(`/docs/${docId}/snapshots/${snapshotId}/restore`);
      pushToast("Snapshot restored.", { variant: "success" });
      await loadSnapshots(docId, setSnapshots);
    } catch (error) {
      pushToast(getApiErrorMessage(error, "Failed to restore snapshot."), { variant: "error" });
    }
  }

  if (!docId) {
    return <div className="screen-center">Missing document id.</div>;
  }

  return (
    <div className="editor-layout">
      <header className="toolbar">
        <button onClick={() => navigate("/docs")}>Back</button>
        <h1>Document {docId}</h1>
        <p>
          role: {role ?? "loading"} | socket: {connectionStatus} | {saveStatus}
        </p>
      </header>
      <main className="editor-main">
        <section className="panel editor-panel">
          {provider && ydocRef.current ? (
            <CollaborativeEditor
              canEdit={canEdit}
              provider={provider}
              ydoc={ydocRef.current}
              user={user}
              onReady={(editor) => {
                editorRef.current = editor;
              }}
            />
          ) : (
            <p>Connecting...</p>
          )}
        </section>
        <aside className="sidebar">
          <PresencePanel users={presenceUsers} connectionStatus={connectionStatus} />
          <CommentsPanel comments={comments} onCreate={createComment} onResolve={resolveComment} onReopen={reopenComment} />
          <SnapshotPanel snapshots={snapshots} onCreate={createSnapshot} onRestore={restoreSnapshot} />
        </aside>
      </main>
    </div>
  );
}

type CollaborativeEditorProps = {
  provider: WebsocketProvider;
  ydoc: Y.Doc;
  user: AuthUser;
  canEdit: boolean;
  onReady: (editor: Editor | null) => void;
};

function CollaborativeEditor({ provider, ydoc, user, canEdit, onReady }: CollaborativeEditorProps) {
  const color = useMemo(() => colorFromUsername(user.username), [user.username]);
  const editor = useEditor(
    {
      editable: canEdit,
      extensions: [
        StarterKit.configure({ history: false }),
        Collaboration.configure({ document: ydoc }),
        CollaborationCursor.configure({
          provider,
          user: {
            name: user.username,
            color,
          },
        }),
      ],
      editorProps: {
        attributes: {
          class: "editor-surface",
        },
      },
    },
    [provider, ydoc, canEdit, color, user.username]
  );

  useEffect(() => {
    onReady(editor);
    return () => onReady(null);
  }, [editor, onReady]);

  if (!editor) {
    return <p>Preparing editor...</p>;
  }

  return <EditorContent editor={editor} />;
}

function buildWsUrl(): string {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const host = window.location.host;
  return `${protocol}://${host}`;
}

function colorFromUsername(username: string): string {
  const palette = ["#ef4444", "#f59e0b", "#10b981", "#3b82f6", "#8b5cf6", "#ec4899"];
  let hash = 0;
  for (let index = 0; index < username.length; index += 1) {
    hash = (hash << 5) - hash + username.charCodeAt(index);
    hash |= 0;
  }
  return palette[Math.abs(hash) % palette.length];
}

async function loadComments(docId: string, setter: (threads: CommentThread[]) => void) {
  const response = await api.get<CommentThread[]>(`/docs/${docId}/comments`);
  setter(response.data);
}

async function loadSnapshots(docId: string, setter: (snapshots: SnapshotRecord[]) => void) {
  const response = await api.get<SnapshotRecord[]>(`/docs/${docId}/snapshots`);
  setter(response.data);
}

function toBase64(data: Uint8Array): string {
  let binary = "";
  data.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return window.btoa(binary);
}
