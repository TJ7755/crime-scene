/**
 * API client for scenario management endpoints.
 */

const REQUEST_TIMEOUT_MS = 7_000;

export interface ScenarioConfig {
  name: string;
  allowed_evidence_types: string[];
  baseline_hypotheses: Record<string, number>;
  default_public_pressure: number;
  turn_pressure_curve: number[];
  evidence_templates: EvidenceTemplate[];
}

export interface EvidenceTemplate {
  id: string;
  category: string;
  base_reliability: number;
  detectability: number;
  manipulability: number;
  current_credibility: number;
  hypothesis_impacts: Record<string, number>;
}

export interface PlayScenarioRequest {
  scenario_id: string;
  seed: number;
  max_turns: number;
}

/**
 * List all available scenarios.
 */
export async function listScenarios(): Promise<string[]> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch("/api/scenarios", {
      method: "GET",
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`Failed to list scenarios: ${response.statusText}`);
    }

    const data = await response.json();
    return data.scenarios || [];
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Get a specific scenario by ID.
 */
export async function getScenario(scenarioId: string): Promise<ScenarioConfig> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(`/api/scenarios/${scenarioId}`, {
      method: "GET",
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`Failed to get scenario: ${response.statusText}`);
    }

    return await response.json();
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Save or update a scenario.
 */
export async function saveScenario(
  scenarioId: string,
  config: ScenarioConfig
): Promise<void> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(`/api/scenarios/${scenarioId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(config),
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`Failed to save scenario: ${response.statusText}`);
    }
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Initialize the game with a specific scenario.
 */
export async function playScenario(request: PlayScenarioRequest): Promise<void> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch("/api/scenarios/play", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`Failed to play scenario: ${response.statusText}`);
    }
  } finally {
    clearTimeout(timeoutId);
  }
}
