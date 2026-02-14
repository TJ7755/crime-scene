import { useCallback, useEffect, useMemo, useState } from "react";
import {
  createEngineAdapter,
  EngineAdapterError,
  type ActionOption,
  type VisibleState,
} from "./api/engineAdapter";
import { ActionBar } from "./components/ActionBar";
import { EvidenceList } from "./components/EvidenceList";
import { FocusView, type FocusMode } from "./components/FocusView";
import { Header } from "./components/Header";
import { PressurePanel } from "./components/PressurePanel";
import { Timeline } from "./components/Timeline";
import { ScenarioEditor } from "./components/ScenarioEditor";

type LeftPanelTab = "evidence" | "timeline";
type ViewMode = "game" | "editor";

const EMPTY_STATE: VisibleState = {
  case_id: "case_001",
  crime_type: "unknown",
  turn: 0,
  status: "active",
  evidence: [],
  timeline: [],
  investigator_signals: {
    priority: "uncertain",
    demeanour: "uncertain",
    recent_shift: "uncertain",
  },
  pressure: {
    public: "uncertain",
    institutional: "uncertain",
    personal: "uncertain",
  },
};

function formatError(error: unknown): string {
  if (error instanceof EngineAdapterError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Unexpected UI error.";
}

/** Renders the dossier UI and coordinates data flow with the engine adapter. */
export default function App() {
  const adapter = useMemo(() => createEngineAdapter(), []);

  const [viewMode, setViewMode] = useState<ViewMode>("game");
  const [visibleState, setVisibleState] = useState<VisibleState | null>(null);
  const [actions, setActions] = useState<ActionOption[]>([]);
  const [leftPanelTab, setLeftPanelTab] = useState<LeftPanelTab>("evidence");
  const [focusMode, setFocusMode] = useState<FocusMode>("summary");
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(null);
  const [selectedTimelineIndex, setSelectedTimelineIndex] = useState(0);
  const [selectedActionId, setSelectedActionId] = useState<string | null>(null);
  const [casePages, setCasePages] = useState<string[]>(["page-a", "page-b", "page-c"]);
  const [activePage, setActivePage] = useState("page-a");
  const [actionResult, setActionResult] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  const hydrate = useCallback(async () => {
    setLoading(true);
    setStatusMessage("");

    try {
      const [stateResponse, actionsResponse, slots] = await Promise.all([
        adapter.getVisibleState(),
        adapter.getActions(),
        adapter.listSlots(),
      ]);

      setVisibleState(stateResponse);
      setActions(actionsResponse.actions);
      setCasePages(slots.length > 0 ? slots : ["page-a", "page-b", "page-c"]);
      setSelectedEvidenceId(stateResponse.evidence[0]?.id ?? null);
      setSelectedTimelineIndex(0);
      setSelectedActionId(actionsResponse.actions[0]?.id ?? null);
    } catch (error) {
      setStatusMessage(formatError(error));
    } finally {
      setLoading(false);
    }
  }, [adapter]);

  useEffect(() => {
    void hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (!visibleState) {
      return;
    }

    if (!visibleState.evidence.some((item) => item.id === selectedEvidenceId)) {
      setSelectedEvidenceId(visibleState.evidence[0]?.id ?? null);
    }

    if (selectedTimelineIndex >= visibleState.timeline.length) {
      setSelectedTimelineIndex(Math.max(0, visibleState.timeline.length - 1));
    }
  }, [visibleState, selectedEvidenceId, selectedTimelineIndex]);

  const handleApplyAction = useCallback(
    async (actionId: string) => {
      setBusy(true);
      setStatusMessage("");
      try {
        const response = await adapter.applyAction({ action_id: actionId, params: {} });
        const refreshedActions = await adapter.getActions();
        setVisibleState(response.visible_state);
        setActions(refreshedActions.actions);
        setSelectedActionId(
          refreshedActions.actions.find((action) => action.id === actionId)?.id ??
            refreshedActions.actions[0]?.id ??
            null,
        );
        setActionResult(response.action_result.summary);
      } catch (error) {
        setStatusMessage(formatError(error));
      } finally {
        setBusy(false);
      }
    },
    [adapter],
  );

  const handleSavePage = useCallback(async () => {
    setBusy(true);
    setStatusMessage("");
    try {
      await adapter.saveSlot(activePage);
      setCasePages(await adapter.listSlots());
      setStatusMessage(`Saved current view to ${activePage}.`);
    } catch (error) {
      setStatusMessage(formatError(error));
    } finally {
      setBusy(false);
    }
  }, [adapter, activePage]);

  const handleLoadPage = useCallback(async () => {
    setBusy(true);
    setStatusMessage("");
    try {
      const loadedState = await adapter.loadSlot(activePage);
      const refreshedActions = await adapter.getActions();
      setVisibleState(loadedState);
      setActions(refreshedActions.actions);
      setSelectedActionId(refreshedActions.actions[0]?.id ?? null);
      setActionResult(`Loaded ${activePage}.`);
    } catch (error) {
      setStatusMessage(formatError(error));
    } finally {
      setBusy(false);
    }
  }, [adapter, activePage]);

  const state = visibleState ?? EMPTY_STATE;
  const selectedEvidence =
    state.evidence.find((item) => item.id === selectedEvidenceId) ?? state.evidence[0] ?? null;
  const selectedTimeline = state.timeline[selectedTimelineIndex] ?? null;

  // Show scenario editor if in editor mode
  if (viewMode === "editor") {
    return (
      <ScenarioEditor
        onClose={() => setViewMode("game")}
        onPlay={async (scenarioId) => {
          setViewMode("game");
          // Reload the game state after playing scenario
          await hydrate();
        }}
      />
    );
  }

  return (
    <div className="dossier-shell">
      <div className="mx-auto max-w-[1600px] px-3 py-3">
        <div className="mb-3 flex items-center justify-between">
          <Header
            caseId={state.case_id}
            crimeType={state.crime_type}
            day={state.turn}
            status={state.status}
            activePage={activePage}
            pages={casePages}
            adapterKind={adapter.kind}
            busy={busy}
            onPageChange={setActivePage}
            onSavePage={handleSavePage}
            onLoadPage={handleLoadPage}
          />
          <button
            type="button"
            onClick={() => setViewMode("editor")}
            className="rounded-md bg-accent-blue px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Scenario Editor
          </button>
        </div>

        <p
          className="mb-2 min-h-6 text-sm text-dossier-700"
          role={statusMessage ? "alert" : "status"}
          aria-live="polite"
        >
          {loading ? "Loading visible state..." : statusMessage}
        </p>

        <div className="grid gap-3 lg:grid-cols-[18rem_minmax(0,1fr)_16rem]">
          <aside className="dossier-panel min-h-[460px]" aria-label="Evidence and timeline">
            <div className="flex gap-2 border-b border-dossier-200 pb-2" role="tablist">
              <button
                type="button"
                role="tab"
                aria-selected={leftPanelTab === "evidence"}
                className={`focus-mode-button ${leftPanelTab === "evidence" ? "bg-dossier-200/70 text-dossier-900" : "bg-white"}`}
                onClick={() => setLeftPanelTab("evidence")}
              >
                Evidence
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={leftPanelTab === "timeline"}
                className={`focus-mode-button ${leftPanelTab === "timeline" ? "bg-dossier-200/70 text-dossier-900" : "bg-white"}`}
                onClick={() => setLeftPanelTab("timeline")}
              >
                Timeline
              </button>
            </div>

            <div className="mt-3">
              {leftPanelTab === "evidence" ? (
                <EvidenceList
                  evidence={state.evidence}
                  selectedId={selectedEvidence?.id ?? null}
                  onSelect={(id) => {
                    setSelectedEvidenceId(id);
                    setFocusMode("evidence");
                  }}
                />
              ) : (
                <Timeline
                  entries={state.timeline}
                  selectedIndex={selectedTimelineIndex}
                  onSelect={(index) => {
                    setSelectedTimelineIndex(index);
                    setFocusMode("summary");
                  }}
                />
              )}
            </div>
          </aside>

          <main>
            <FocusView
              mode={focusMode}
              state={state}
              selectedEvidence={selectedEvidence}
              selectedTimeline={selectedTimeline}
              onModeChange={setFocusMode}
            />
          </main>

          <aside>
            <PressurePanel pressure={state.pressure} />
          </aside>
        </div>

        <ActionBar
          actions={actions}
          selectedActionId={selectedActionId}
          busy={busy}
          actionResult={actionResult}
          onSelectAction={setSelectedActionId}
          onApplyAction={handleApplyAction}
        />
      </div>
    </div>
  );
}
