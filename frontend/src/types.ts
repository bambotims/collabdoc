export interface AuthUser {
  id: number;
  username: string;
  email: string;
}

export interface DocumentRecord {
  id: string;
  title: string;
  owner_id: number;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  my_role: "owner" | "editor" | "commenter" | "viewer";
}

export interface CommentThread {
  id: number;
  document_id: string;
  author_id: number;
  body: string;
  status: "open" | "resolved";
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  resolved_by_id: number | null;
  anchor: {
    start_rel_b64: string;
    end_rel_b64: string;
  };
}

export interface SnapshotRecord {
  id: number;
  document_id: string;
  seq: number;
  kind: "manual" | "scheduled" | "restore";
  created_by_id: number | null;
  metadata: Record<string, unknown>;
  created_at: string;
}
