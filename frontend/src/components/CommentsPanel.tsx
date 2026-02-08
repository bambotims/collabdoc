import type { CommentThread } from "../types";

type CommentsPanelProps = {
  comments: CommentThread[];
  onCreate: (body: string) => Promise<void>;
  onResolve: (threadId: number) => Promise<void>;
  onReopen: (threadId: number) => Promise<void>;
};

export function CommentsPanel({ comments, onCreate, onResolve, onReopen }: CommentsPanelProps) {
  return (
    <section className="panel sidebar-section">
      <h3>Comments</h3>
      <CommentForm onCreate={onCreate} />
      <ul className="comment-list">
        {comments.map((thread) => (
          <li key={thread.id}>
            <p>{thread.body}</p>
            <p className="muted">status: {thread.status}</p>
            {thread.status === "open" ? (
              <button onClick={() => void onResolve(thread.id)}>Resolve</button>
            ) : (
              <button onClick={() => void onReopen(thread.id)}>Reopen</button>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

type CommentFormProps = {
  onCreate: (body: string) => Promise<void>;
};

function CommentForm({ onCreate }: CommentFormProps) {
  let input = "";

  return (
    <form
      className="comment-form"
      onSubmit={(event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const field = form.elements.namedItem("comment_body") as HTMLInputElement;
        input = field.value.trim();
        if (!input) {
          return;
        }
        void onCreate(input).then(() => {
          field.value = "";
        });
      }}
    >
      <input name="comment_body" placeholder="Add comment" />
      <button type="submit">Send</button>
    </form>
  );
}
