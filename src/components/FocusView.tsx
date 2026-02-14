import type { EvidenceItem, TimelineItem, VisibleState } from "../api/engineAdapter";

export type FocusMode = "summary" | "evidence" | "signals";

interface FocusViewProps {
  mode: FocusMode;
  state: VisibleState;
  selectedEvidence: EvidenceItem | null;
  selectedTimeline: TimelineItem | null;
  onModeChange: (mode: FocusMode) => void;
}

function formatToken(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

/** Renders the center panel for case summary, evidence detail, and investigator signals. */
export function FocusView({
  mode,
  state,
  selectedEvidence,
  selectedTimeline,
  onModeChange,
}: FocusViewProps) {
  const surfacedCount = state.evidence.filter((item) => item.state === "surfaced").length;

  return (
    <section className="dossier-panel min-h-[460px]" aria-label="Focus view">
      <div className="mb-3 flex flex-wrap gap-2 border-b border-dossier-200 pb-2">
        <button
          type="button"
          className={`focus-mode-button ${mode === "summary" ? "bg-dossier-200/70 text-dossier-900" : "bg-white"}`}
          onClick={() => onModeChange("summary")}
        >
          Case Summary
        </button>
        <button
          type="button"
          className={`focus-mode-button ${mode === "evidence" ? "bg-dossier-200/70 text-dossier-900" : "bg-white"}`}
          onClick={() => onModeChange("evidence")}
        >
          Evidence Raw
        </button>
        <button
          type="button"
          className={`focus-mode-button ${mode === "signals" ? "bg-dossier-200/70 text-dossier-900" : "bg-white"}`}
          onClick={() => onModeChange("signals")}
        >
          Investigator Signals
        </button>
      </div>

      {mode === "summary" && (
        <div className="space-y-4">
          <article className="rounded-sm border border-dossier-200 bg-white/80 p-3">
            <p className="dossier-label">Current Snapshot</p>
            <dl className="mt-2 grid gap-3 sm:grid-cols-2">
              <div>
                <dt className="text-xs text-dossier-500">Visible Evidence</dt>
                <dd className="text-sm font-semibold text-dossier-900">{state.evidence.length}</dd>
              </div>
              <div>
                <dt className="text-xs text-dossier-500">Surfaced Items</dt>
                <dd className="text-sm font-semibold text-dossier-900">{surfacedCount}</dd>
              </div>
              <div>
                <dt className="text-xs text-dossier-500">Timeline Events</dt>
                <dd className="text-sm font-semibold text-dossier-900">{state.timeline.length}</dd>
              </div>
              <div>
                <dt className="text-xs text-dossier-500">Case Status</dt>
                <dd className="text-sm font-semibold text-dossier-900">{formatToken(state.status)}</dd>
              </div>
            </dl>
          </article>

          {selectedTimeline && (
            <article className="rounded-sm border border-dossier-200 bg-white/80 p-3">
              <p className="dossier-label">Selected Timeline Event</p>
              <p className="mt-2 text-sm font-semibold text-dossier-900">
                {formatToken(selectedTimeline.label)}
              </p>
              <p className="mt-1 text-sm text-dossier-700">{selectedTimeline.details}</p>
            </article>
          )}
        </div>
      )}

      {mode === "evidence" && (
        <div className="space-y-4">
          {selectedEvidence ? (
            <>
              <article className="rounded-sm border border-dossier-200 bg-white/80 p-3">
                <p className="dossier-label">Evidence Item</p>
                <h2 className="mt-2 text-lg font-semibold text-dossier-900">{selectedEvidence.label}</h2>
                <dl className="mt-2 grid gap-3 sm:grid-cols-2">
                  <div>
                    <dt className="text-xs text-dossier-500">Category</dt>
                    <dd className="text-sm text-dossier-800">{formatToken(selectedEvidence.category)}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-dossier-500">Discovery State</dt>
                    <dd className="text-sm text-dossier-800">{formatToken(selectedEvidence.state)}</dd>
                  </div>
                </dl>
                <p className="mt-3 text-sm leading-relaxed text-dossier-700">{selectedEvidence.summary}</p>
              </article>

              <article className="rounded-sm border border-dossier-200 bg-dossier-50/80 p-3">
                <p className="dossier-label">Sensitive Snippet</p>
                <div className="mt-2 space-y-2">
                  <span className="redaction-bar w-11/12" />
                  <span className="redaction-bar w-9/12" />
                  <span className="redaction-bar w-10/12" />
                  <span className="sr-only">Sensitive text is redacted.</span>
                </div>
              </article>
            </>
          ) : (
            <p className="text-sm text-dossier-600">Select an evidence item to inspect details.</p>
          )}
        </div>
      )}

      {mode === "signals" && (
        <article className="rounded-sm border border-dossier-200 bg-white/80 p-3">
          <p className="dossier-label">Behaviour Signals</p>
          <dl className="mt-3 space-y-3">
            <div className="rounded-sm border border-dossier-100 bg-dossier-50/70 p-2">
              <dt className="text-xs text-dossier-500">Priority</dt>
              <dd className="text-sm font-medium text-dossier-900">
                {formatToken(state.investigator_signals.priority)}
              </dd>
            </div>
            <div className="rounded-sm border border-dossier-100 bg-dossier-50/70 p-2">
              <dt className="text-xs text-dossier-500">Demeanour</dt>
              <dd className="text-sm font-medium text-dossier-900">
                {formatToken(state.investigator_signals.demeanour)}
              </dd>
            </div>
            <div className="rounded-sm border border-dossier-100 bg-dossier-50/70 p-2">
              <dt className="text-xs text-dossier-500">Recent Shift</dt>
              <dd className="text-sm font-medium text-dossier-900">
                {formatToken(state.investigator_signals.recent_shift)}
              </dd>
            </div>
          </dl>
        </article>
      )}
    </section>
  );
}
