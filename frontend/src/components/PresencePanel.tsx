type PresenceUser = {
  clientId: string;
  name: string;
  color: string;
};

type PresencePanelProps = {
  users: PresenceUser[];
  connectionStatus: string;
};

export function PresencePanel({ users, connectionStatus }: PresencePanelProps) {
  return (
    <section className="panel sidebar-section">
      <h3>Presence</h3>
      <p className="muted">socket: {connectionStatus}</p>
      <ul className="presence-list">
        {users.map((user) => (
          <li key={user.clientId}>
            <span className="presence-dot" style={{ background: user.color }} />
            {user.name}
          </li>
        ))}
      </ul>
    </section>
  );
}

export type { PresenceUser };
