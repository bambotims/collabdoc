import type { SnapshotRecord } from "../types";

type SnapshotPanelProps = {
  snapshots: SnapshotRecord[];
  onCreate: () => Promise<void>;
  onRestore: (snapshotId: number) => Promise<void>;
};

export function SnapshotPanel({ snapshots, onCreate, onRestore }: SnapshotPanelProps) {
  return (
    <section className="panel sidebar-section">
      <h3>Snapshots</h3>
      <button onClick={() => void onCreate()}>Create snapshot</button>
      <ul className="snapshot-list">
        {snapshots.map((snapshot) => (
          <li key={snapshot.id}>
            <p>#{snapshot.id} seq {snapshot.seq} ({snapshot.kind})</p>
            <button onClick={() => void onRestore(snapshot.id)}>Restore</button>
          </li>
        ))}
      </ul>
    </section>
  );
}
