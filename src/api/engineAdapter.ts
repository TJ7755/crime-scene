const QUALITATIVE_TERMS = new Set([
  "low",
  "moderate",
  "elevated",
  "high",
  "critical",
  "uncertain",
  "probable",
  "contradictory",
  "stable",
  "fragile",
]);

const STATUS_TERMS = new Set(["active", "contained", "paused", "cold", "closed"]);
const EVIDENCE_STATES = new Set(["surfaced", "logged", "review", "suppressed", "archived"]);
const REQUEST_TIMEOUT_MS = 7_000;
const DEFAULT_SLOTS = ["page-a", "page-b", "page-c"];
const RESTRICTED_TEXT_PATTERN =
  /\b(seed|rng|debug|hypothesis|belief|suspicion|credibility|confidence|likelihood|probability)\b|\d+(\.\d+)?%/i;

export type PressureLabel =
  | "low"
  | "moderate"
  | "elevated"
  | "high"
  | "critical"
  | "uncertain"
  | "probable"
  | "contradictory"
  | "stable"
  | "fragile";

export interface EvidenceItem {
  id: string;
  label: string;
  category: string;
  state: string;
  summary: string;
}

export interface TimelineItem {
  time: string;
  label: string;
  details: string;
}

export interface InvestigatorSignals {
  priority: string;
  demeanour: string;
  recent_shift: string;
}

export interface PressureState {
  public: PressureLabel;
  institutional: PressureLabel;
  personal: PressureLabel;
}

export interface VisibleState {
  case_id: string;
  crime_type: string;
  turn: number;
  status: string;
  evidence: EvidenceItem[];
  timeline: TimelineItem[];
  investigator_signals: InvestigatorSignals;
  pressure: PressureState;
}

export interface ActionOption {
  id: string;
  label: string;
  enabled: boolean;
  cost?: string;
  desc: string;
  disabled_reason?: string;
}

export interface ActionsResponse {
  actions: ActionOption[];
}

export interface ApplyActionRequest {
  action_id: string;
  params?: Record<string, unknown>;
}

export interface ActionResult {
  success: boolean;
  summary: string;
}

export interface ApplyActionResponse {
  visible_state: VisibleState;
  action_result: ActionResult;
}

export interface EngineAdapter {
  kind: "live" | "mock";
  getVisibleState: () => Promise<VisibleState>;
  getActions: () => Promise<ActionsResponse>;
  applyAction: (request: ApplyActionRequest) => Promise<ApplyActionResponse>;
  saveSlot: (slotId: string) => Promise<void>;
  loadSlot: (slotId: string) => Promise<VisibleState>;
  listSlots: () => Promise<string[]>;
}

export class EngineAdapterError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "EngineAdapterError";
  }
}

function deepClone<T>(value: T): T {
  if (typeof structuredClone === "function") {
    return structuredClone(value);
  }
  return JSON.parse(JSON.stringify(value)) as T;
}

function clampText(value: unknown, fallback: string, limit = 180, redactRestricted = false): string {
  if (typeof value !== "string") {
    return fallback;
  }
  const normalized = value.trim().replace(/\s+/g, " ");
  if (!normalized) {
    return fallback;
  }
  if (redactRestricted && RESTRICTED_TEXT_PATTERN.test(normalized)) {
    return "Restricted in visible state.";
  }
  return normalized.slice(0, limit);
}

function sanitizeDescriptor(value: unknown, fallback = "uncertain"): string {
  const candidate = clampText(value, fallback, 64).toLowerCase().replace(/\s+/g, "_");
  if (/\d/.test(candidate)) {
    return fallback;
  }
  if (
    candidate.includes("seed") ||
    candidate.includes("rng") ||
    candidate.includes("debug") ||
    candidate.includes("belief") ||
    candidate.includes("hypothesis")
  ) {
    return fallback;
  }
  if (!/^[a-z_-]+$/.test(candidate)) {
    return fallback;
  }
  return candidate;
}

function sanitizeStatus(value: unknown): string {
  const status = sanitizeDescriptor(value, "active");
  return STATUS_TERMS.has(status) ? status : "active";
}

function sanitizePressure(value: unknown): PressureLabel {
  const pressure = sanitizeDescriptor(value, "uncertain") as PressureLabel;
  return QUALITATIVE_TERMS.has(pressure) ? pressure : "uncertain";
}

function sanitizeIsoTime(value: unknown): string {
  const text = clampText(value, "", 48);
  if (!text) {
    return new Date(Date.UTC(2026, 1, 1, 0, 0, 0)).toISOString();
  }
  const date = new Date(text);
  if (Number.isNaN(date.getTime())) {
    return new Date(Date.UTC(2026, 1, 1, 0, 0, 0)).toISOString();
  }
  return date.toISOString();
}

function sanitizeEvidence(item: unknown, index: number): EvidenceItem {
  const payload = item as Record<string, unknown>;
  const state = sanitizeDescriptor(payload?.state, "logged");
  return {
    id: clampText(payload?.id, `e${index + 1}`, 32),
    label: clampText(payload?.label, `Evidence ${index + 1}`, 70),
    category: sanitizeDescriptor(payload?.category, "general"),
    state: EVIDENCE_STATES.has(state) ? state : "logged",
    summary: clampText(payload?.summary, "No summary available.", 220, true),
  };
}

function sanitizeTimeline(item: unknown, index: number): TimelineItem {
  const payload = item as Record<string, unknown>;
  return {
    time: sanitizeIsoTime(payload?.time),
    label: clampText(payload?.label, `event_${index + 1}`, 60),
    details: clampText(payload?.details, "No details provided.", 240, true),
  };
}

function sanitizeVisibleState(input: unknown): VisibleState {
  const payload = input as Record<string, unknown>;
  const evidenceSource = Array.isArray(payload?.evidence) ? payload.evidence : [];
  const timelineSource = Array.isArray(payload?.timeline) ? payload.timeline : [];
  const signals = (payload?.investigator_signals ?? {}) as Record<string, unknown>;
  const pressure = (payload?.pressure ?? {}) as Record<string, unknown>;
  const rawTurn = Number(payload?.turn);
  const turn = Number.isFinite(rawTurn) && rawTurn >= 0 ? Math.floor(rawTurn) : 0;

  return {
    case_id: clampText(payload?.case_id, "case_001", 40),
    crime_type: sanitizeDescriptor(payload?.crime_type, "unknown"),
    turn,
    status: sanitizeStatus(payload?.status),
    evidence: evidenceSource.map((item, index) => sanitizeEvidence(item, index)),
    timeline: timelineSource.map((item, index) => sanitizeTimeline(item, index)),
    investigator_signals: {
      priority: sanitizeDescriptor(signals.priority, "uncertain"),
      demeanour: sanitizeDescriptor(signals.demeanour, "uncertain"),
      recent_shift: sanitizeDescriptor(signals.recent_shift, "uncertain"),
    },
    pressure: {
      public: sanitizePressure(pressure.public),
      institutional: sanitizePressure(pressure.institutional),
      personal: sanitizePressure(pressure.personal),
    },
  };
}

function sanitizeAction(item: unknown, index: number): ActionOption {
  const payload = item as Record<string, unknown>;
  const enabled = Boolean(payload?.enabled);
  const disabledReason = enabled
    ? undefined
    : clampText(
        payload?.disabled_reason,
        "Unavailable this turn due to current case conditions.",
        120,
        true,
      );

  return {
    id: clampText(payload?.id, `action_${index + 1}`, 64),
    label: clampText(payload?.label, `Action ${index + 1}`, 80),
    enabled,
    cost: typeof payload?.cost === "string" ? clampText(payload.cost, "", 20) : undefined,
    desc: clampText(payload?.desc, "No description available.", 200, true),
    disabled_reason: disabledReason,
  };
}

function sanitizeActionsResponse(input: unknown): ActionsResponse {
  const payload = input as Record<string, unknown>;
  const actions = Array.isArray(payload?.actions) ? payload.actions : [];
  return { actions: actions.map((item, index) => sanitizeAction(item, index)) };
}

function sanitizeActionResult(input: unknown): ActionResult {
  const payload = input as Record<string, unknown>;
  return {
    success: Boolean(payload?.success),
    summary: clampText(payload?.summary, "Action completed.", 220, true),
  };
}

async function formatResponseError(response: Response): Promise<string> {
  const text = (await response.text()).trim();
  if (!text) {
    return `Engine request failed (${response.status}).`;
  }
  return `Engine request failed (${response.status}): ${text.slice(0, 220)}`;
}

async function fetchJson<T>(apiBase: string, path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  const url = `${apiBase}${path}`;

  try {
    const response = await fetch(url, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new EngineAdapterError(await formatResponseError(response));
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof EngineAdapterError) {
      throw error;
    }
    if (error instanceof Error && error.name === "AbortError") {
      throw new EngineAdapterError("Engine request timed out. Please retry.");
    }
    throw new EngineAdapterError("Engine request failed. Check API base URL and connectivity.");
  } finally {
    clearTimeout(timeout);
  }
}

function createLiveAdapter(apiBase: string): EngineAdapter {
  const slots = new Map<string, VisibleState>();
  let current: VisibleState | null = null;

  return {
    kind: "live",
    getVisibleState: async () => {
      const payload = await fetchJson<unknown>(apiBase, "/api/visible_state");
      current = sanitizeVisibleState(payload);
      return deepClone(current);
    },
    getActions: async () => {
      const payload = await fetchJson<unknown>(apiBase, "/api/actions");
      return sanitizeActionsResponse(payload);
    },
    applyAction: async (request) => {
      const payload = await fetchJson<unknown>(apiBase, "/api/apply_action", {
        method: "POST",
        body: JSON.stringify({
          action_id: request.action_id,
          params: request.params ?? {},
        }),
      });

      const raw = payload as Record<string, unknown>;
      const visibleState = sanitizeVisibleState(raw.visible_state);
      const actionResult = sanitizeActionResult(raw.action_result);
      current = visibleState;

      return {
        visible_state: deepClone(visibleState),
        action_result: actionResult,
      };
    },
    saveSlot: async (slotId) => {
      if (!current) {
        return;
      }
      slots.set(slotId, deepClone(current));
    },
    loadSlot: async (slotId) => {
      const snapshot = slots.get(slotId);
      if (!snapshot) {
        throw new EngineAdapterError(`No saved data for "${slotId}". Save a page first.`);
      }
      current = deepClone(snapshot);
      return deepClone(snapshot);
    },
    listSlots: async () => deepClone(DEFAULT_SLOTS),
  };
}

/** Returns a deterministic numeric seed parsed from the current URL query string. */
export function getSeedFromUrl(search?: string): number {
  const source =
    typeof search === "string"
      ? search
      : typeof window !== "undefined"
        ? window.location.search
        : "";
  const params = new URLSearchParams(source);
  const parsed = Number.parseInt(params.get("seed") ?? "1", 10);
  if (!Number.isFinite(parsed) || parsed === 0) {
    return 1;
  }
  return Math.abs(parsed);
}

function createMulberry32(seed: number): () => number {
  let value = seed >>> 0;
  return () => {
    value += 0x6d2b79f5;
    let temp = Math.imul(value ^ (value >>> 15), value | 1);
    temp ^= temp + Math.imul(temp ^ (temp >>> 7), temp | 61);
    return ((temp ^ (temp >>> 14)) >>> 0) / 4294967296;
  };
}

function pickFrom<T>(items: T[], rng: () => number): T {
  return items[Math.floor(rng() * items.length)];
}

function shiftPressure(current: PressureLabel, delta: number): PressureLabel {
  const scale: PressureLabel[] = ["low", "moderate", "elevated", "high", "critical"];
  const index = scale.indexOf(current);
  if (index < 0) {
    return "uncertain";
  }
  const next = Math.max(0, Math.min(scale.length - 1, index + delta));
  return scale[next];
}

function createInitialMockState(seed: number): VisibleState {
  const rng = createMulberry32(seed);
  const crimeType = pickFrom(["murder", "fraud", "arson", "kidnapping"], rng);
  const caseId = `case_${String((seed % 900) + 100).padStart(3, "0")}`;

  const evidence: EvidenceItem[] = [
    {
      id: "e1",
      label: "CCTV Clip",
      category: "digital",
      state: "surfaced",
      summary: "Partial frame captured; vehicle profile remains uncertain.",
    },
    {
      id: "e2",
      label: "Station Ledger",
      category: "document",
      state: rng() > 0.5 ? "surfaced" : "logged",
      summary: "Entry sequence has one contradictory time-stamp.",
    },
    {
      id: "e3",
      label: "Lab Swab",
      category: "forensic",
      state: "review",
      summary: "Residue profile linked to probable transfer contact.",
    },
    {
      id: "e4",
      label: "Witness Call",
      category: "witness",
      state: rng() > 0.5 ? "logged" : "review",
      summary: "Caller timeline is probable but partially contradictory.",
    },
  ];

  const timeline: TimelineItem[] = [
    {
      time: "2026-02-01T20:40:00.000Z",
      label: "incident",
      details: "Incident logged by control room.",
    },
    {
      time: "2026-02-01T21:15:00.000Z",
      label: "first_response",
      details: "Initial perimeter established.",
    },
    {
      time: "2026-02-01T22:00:00.000Z",
      label: "evidence_intake",
      details: "Initial digital and physical evidence intake completed.",
    },
  ];

  return {
    case_id: caseId,
    crime_type: crimeType,
    turn: 1 + Math.floor(rng() * 3),
    status: "active",
    evidence,
    timeline,
    investigator_signals: {
      priority: pickFrom(["forensics", "interviews", "financial", "surveillance"], rng),
      demeanour: pickFrom(["controlled", "impatient", "guarded", "methodical"], rng),
      recent_shift: pickFrom(
        ["attention_narrowing", "scope_balancing", "risk_avoidance"],
        rng,
      ),
    },
    pressure: {
      public: pickFrom(["low", "moderate", "elevated"], rng),
      institutional: pickFrom(["low", "moderate"], rng),
      personal: pickFrom(["moderate", "elevated"], rng),
    },
  };
}

function buildMockActions(state: VisibleState): ActionsResponse {
  const surfacedCount = state.evidence.filter((item) => item.state === "surfaced").length;
  const hasSuppressed = state.evidence.some((item) => item.state === "suppressed");
  const canDelay = state.pressure.public !== "critical";

  return {
    actions: [
      {
        id: "remove_evidence",
        label: "Remove Evidence",
        enabled: surfacedCount > 0,
        cost: "£200",
        desc: "Move one surfaced item into restricted review.",
        disabled_reason:
          surfacedCount > 0 ? undefined : "No surfaced evidence is available to remove.",
      },
      {
        id: "delay_briefing",
        label: "Delay Briefing",
        enabled: canDelay,
        cost: "£0",
        desc: "Delay the official briefing by one turn.",
        disabled_reason: canDelay ? undefined : "Public pressure is too high to delay briefing.",
      },
      {
        id: "reframe_priority",
        label: "Reframe Priority",
        enabled: true,
        cost: "£0",
        desc: "Cycle investigator focus to the next discipline.",
      },
      {
        id: "seal_archive",
        label: "Seal Archive",
        enabled: hasSuppressed,
        cost: "£120",
        desc: "Seal one suppressed record into archive storage.",
        disabled_reason: hasSuppressed
          ? undefined
          : "At least one suppressed item is needed before sealing archive.",
      },
    ],
  };
}

function appendTimeline(state: VisibleState, label: string, details: string): TimelineItem[] {
  const eventTime = new Date(Date.UTC(2026, 1, 1, 20 + state.turn, 10, 0)).toISOString();
  return [
    ...state.timeline,
    {
      time: eventTime,
      label,
      details,
    },
  ].slice(-12);
}

function applyMockAction(state: VisibleState, actionId: string): ApplyActionResponse {
  const next = deepClone(state);

  if (actionId === "remove_evidence") {
    const targetIndex = next.evidence.findIndex((item) => item.state === "surfaced");
    if (targetIndex < 0) {
      return {
        visible_state: next,
        action_result: {
          success: false,
          summary: "No surfaced evidence could be moved.",
        },
      };
    }
    next.turn += 1;
    next.evidence[targetIndex] = {
      ...next.evidence[targetIndex],
      state: "suppressed",
      summary: "Access restricted pending compliance review.",
    };
    next.pressure.public = shiftPressure(next.pressure.public, 1);
    next.timeline = appendTimeline(
      next,
      "evidence_removed",
      "One surfaced evidence item moved into restricted review.",
    );
    return {
      visible_state: next,
      action_result: {
        success: true,
        summary: "Evidence moved to restricted review for this cycle.",
      },
    };
  }

  if (actionId === "delay_briefing") {
    if (next.pressure.public === "critical") {
      return {
        visible_state: next,
        action_result: {
          success: false,
          summary: "Briefing delay rejected under critical public pressure.",
        },
      };
    }
    next.turn += 1;
    next.pressure.public = shiftPressure(next.pressure.public, -1);
    next.pressure.institutional = shiftPressure(next.pressure.institutional, 1);
    next.timeline = appendTimeline(
      next,
      "briefing_delayed",
      "Official briefing pushed by one operational cycle.",
    );
    return {
      visible_state: next,
      action_result: {
        success: true,
        summary: "Briefing delayed; institutional pressure increased.",
      },
    };
  }

  if (actionId === "reframe_priority") {
    const priorities = ["forensics", "interviews", "financial", "surveillance"];
    const currentIndex = priorities.indexOf(next.investigator_signals.priority);
    const nextIndex = currentIndex < 0 ? 0 : (currentIndex + 1) % priorities.length;
    next.turn += 1;
    next.investigator_signals.priority = priorities[nextIndex];
    next.investigator_signals.recent_shift = "attention_realignment";
    next.timeline = appendTimeline(
      next,
      "priority_reframed",
      `Investigator priority shifted to ${priorities[nextIndex]}.`,
    );
    return {
      visible_state: next,
      action_result: {
        success: true,
        summary: `Priority shifted to ${priorities[nextIndex]}.`,
      },
    };
  }

  if (actionId === "seal_archive") {
    const targetIndex = next.evidence.findIndex((item) => item.state === "suppressed");
    if (targetIndex < 0) {
      return {
        visible_state: next,
        action_result: {
          success: false,
          summary: "No suppressed item available for archive sealing.",
        },
      };
    }
    next.turn += 1;
    next.evidence[targetIndex] = {
      ...next.evidence[targetIndex],
      state: "archived",
      summary: "Record sealed in archive.",
    };
    next.pressure.institutional = shiftPressure(next.pressure.institutional, -1);
    next.timeline = appendTimeline(
      next,
      "archive_sealed",
      "Suppressed record sealed in archive storage.",
    );
    return {
      visible_state: next,
      action_result: {
        success: true,
        summary: "Archive seal completed for one restricted record.",
      },
    };
  }

  return {
    visible_state: next,
    action_result: {
      success: false,
      summary: "Action not recognized by mock adapter.",
    },
  };
}

function createMockAdapter(seed: number): EngineAdapter {
  let state = createInitialMockState(seed);
  const slots = new Map<string, VisibleState>();

  return {
    kind: "mock",
    getVisibleState: async () => deepClone(state),
    getActions: async () => deepClone(buildMockActions(state)),
    applyAction: async (request) => {
      const response = applyMockAction(state, request.action_id);
      state = deepClone(response.visible_state);
      return deepClone(response);
    },
    saveSlot: async (slotId) => {
      slots.set(slotId, deepClone(state));
    },
    loadSlot: async (slotId) => {
      const snapshot = slots.get(slotId);
      if (!snapshot) {
        throw new EngineAdapterError(`No saved data for "${slotId}". Save a page first.`);
      }
      state = deepClone(snapshot);
      return deepClone(snapshot);
    },
    listSlots: async () => {
      const merged = new Set([...DEFAULT_SLOTS, ...slots.keys()]);
      return Array.from(merged);
    },
  };
}

/** Creates the engine adapter instance used by the UI. */
export function createEngineAdapter(): EngineAdapter {
  // Set VITE_ENGINE_API_BASE to point at the live Python engine, for example http://localhost:8000.
  const apiBase = (import.meta.env.VITE_ENGINE_API_BASE ?? "")
    .toString()
    .trim()
    .replace(/\/$/, "");
  const useMock = (import.meta.env.VITE_USE_MOCK ?? "true").toString().toLowerCase() !== "false";

  if (useMock || !apiBase) {
    return createMockAdapter(getSeedFromUrl());
  }
  return createLiveAdapter(apiBase);
}
