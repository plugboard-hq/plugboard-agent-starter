import { theme, ui } from "@plugboard/sdk";

const { Pane, TableView } = ui;

/**
 * Starter's own view of a dataset it produced. ctx brings artifact, dataset,
 * conversationUuid, agentTitle and onClose. Style with the SDK's theme tokens;
 * the host's Tailwind classes are not compiled for bundles.
 */
export default function StarterPane({ artifact, dataset, agentTitle, onClose }) {
  const rows = dataset?.rows || [];
  return (
    <Pane title={artifact.title} subtitle={`${agentTitle || "Starter"} · ${artifact.id} · ${rows.length} rows`} onClose={typeof onClose === "function" ? onClose : undefined}>
      {!dataset && <div style={{ padding: "16px 20px", color: theme.muted, fontSize: 14 }}>Loading…</div>}
      {dataset && <TableView widget={{ ...dataset, total_rows: rows.length }} bare />}
    </Pane>
  );
}
