import type { ActionOption } from "../api/engineAdapter";

interface ActionBarProps {
  actions: ActionOption[];
  selectedActionId: string | null;
  busy: boolean;
  actionResult: string;
  onSelectAction: (actionId: string) => void;
  onApplyAction: (actionId: string) => Promise<void>;
}

/** Renders action buttons and an inline detail pane for the currently selected action. */
export function ActionBar({
  actions,
  selectedActionId,
  busy,
  actionResult,
  onSelectAction,
  onApplyAction,
}: ActionBarProps) {
  const selectedAction = actions.find((action) => action.id === selectedActionId) ?? null;

  return (
    <section className="dossier-panel mt-3" aria-label="Action controls">
      <h2 className="dossier-label">Action Bar</h2>
      <div
        className="mt-2 flex gap-2 overflow-x-auto pb-1"
        role="toolbar"
        aria-label="Available actions"
      >
        {actions.map((action) => {
          const isSelected = action.id === selectedActionId;
          return (
            <button
              key={action.id}
              type="button"
              onClick={() => onSelectAction(action.id)}
              aria-pressed={isSelected}
              className={`min-w-[150px] rounded-sm border px-3 py-2 text-left text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-blue ${
                isSelected
                  ? "border-accent-blue bg-dossier-200/70 text-dossier-900"
                  : "border-dossier-300 bg-white/90 text-dossier-800 hover:bg-dossier-50"
              }`}
            >
              <span className="block font-semibold">{action.label}</span>
              <span className="mt-1 block text-xs text-dossier-500">
                {action.enabled ? action.cost ?? "No cost" : "Unavailable"}
              </span>
            </button>
          );
        })}
      </div>

      <div className="mt-3 rounded-sm border border-dossier-200 bg-white/85 p-3">
        {selectedAction ? (
          <>
            <p className="text-sm font-semibold text-dossier-900">{selectedAction.label}</p>
            <p className="mt-1 text-sm text-dossier-700">{selectedAction.desc}</p>
            <p className="mt-2 text-xs text-dossier-500">
              Cost: <span className="font-medium text-dossier-700">{selectedAction.cost ?? "None"}</span>
            </p>
            {!selectedAction.enabled && (
              <p className="mt-2 text-xs font-medium text-accent-red">
                Why unavailable: {selectedAction.disabled_reason}
              </p>
            )}
            <button
              type="button"
              className="mt-3 rounded-sm border border-dossier-300 bg-dossier-700 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-dossier-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-blue disabled:cursor-not-allowed disabled:opacity-50"
              disabled={!selectedAction.enabled || busy}
              onClick={() => onApplyAction(selectedAction.id)}
            >
              {busy ? "Applying..." : "Apply Action"}
            </button>
          </>
        ) : (
          <p className="text-sm text-dossier-600">Select an action to view details.</p>
        )}

        {actionResult && (
          <p className="mt-3 rounded-sm border border-dossier-200 bg-dossier-50 px-2 py-1 text-xs text-dossier-700">
            Last result: {actionResult}
          </p>
        )}
      </div>
    </section>
  );
}
