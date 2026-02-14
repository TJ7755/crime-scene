import { useEffect, useState } from "react";
import {
  getScenario,
  listScenarios,
  playScenario,
  saveScenario,
  type EvidenceTemplate,
  type ScenarioConfig,
} from "../api/scenarioAdapter";

interface ScenarioEditorProps {
  onClose: () => void;
  onPlay: (scenarioId: string) => void;
}

export function ScenarioEditor({ onClose, onPlay }: ScenarioEditorProps) {
  const [scenarios, setScenarios] = useState<string[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>("");
  const [config, setConfig] = useState<ScenarioConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string>("");
  const [successMessage, setSuccessMessage] = useState<string>("");

  // Load list of scenarios on mount
  useEffect(() => {
    loadScenarioList();
  }, []);

  async function loadScenarioList() {
    try {
      setLoading(true);
      const list = await listScenarios();
      setScenarios(list);
      if (list.length > 0 && !selectedScenario) {
        setSelectedScenario(list[0]);
        await loadScenario(list[0]);
      }
    } catch (err) {
      setError(`Failed to load scenarios: ${err}`);
    } finally {
      setLoading(false);
    }
  }

  async function loadScenario(scenarioId: string) {
    try {
      setLoading(true);
      setError("");
      const loadedConfig = await getScenario(scenarioId);
      setConfig(loadedConfig);
    } catch (err) {
      setError(`Failed to load scenario: ${err}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleScenarioChange(scenarioId: string) {
    setSelectedScenario(scenarioId);
    await loadScenario(scenarioId);
  }

  async function handleSave() {
    if (!config || !selectedScenario) return;

    try {
      setSaving(true);
      setError("");
      setSuccessMessage("");
      await saveScenario(selectedScenario, config);
      setSuccessMessage("Scenario saved successfully!");
      setTimeout(() => setSuccessMessage(""), 3000);
    } catch (err) {
      setError(`Failed to save scenario: ${err}`);
    } finally {
      setSaving(false);
    }
  }

  async function handlePlay() {
    if (!selectedScenario) return;

    try {
      setLoading(true);
      setError("");
      await playScenario({
        scenario_id: selectedScenario,
        seed: Math.floor(Math.random() * 1000000) + 1,
        max_turns: 20,
      });
      onPlay(selectedScenario);
    } catch (err) {
      setError(`Failed to start game: ${err}`);
    } finally {
      setLoading(false);
    }
  }

  function updateConfig(updates: Partial<ScenarioConfig>) {
    if (!config) return;
    setConfig({ ...config, ...updates });
  }

  function updateHypothesis(key: string, value: number) {
    if (!config) return;
    setConfig({
      ...config,
      baseline_hypotheses: {
        ...config.baseline_hypotheses,
        [key]: value,
      },
    });
  }

  function updateEvidenceTemplate(index: number, updates: Partial<EvidenceTemplate>) {
    if (!config) return;
    const newTemplates = [...config.evidence_templates];
    newTemplates[index] = { ...newTemplates[index], ...updates };
    setConfig({ ...config, evidence_templates: newTemplates });
  }

  function addEvidenceTemplate() {
    if (!config) return;
    const newTemplate: EvidenceTemplate = {
      id: `ev_new_${Date.now()}`,
      category: "physical",
      base_reliability: 0.5,
      detectability: 0.5,
      manipulability: 0.5,
      current_credibility: 0.5,
      hypothesis_impacts: {},
    };
    setConfig({
      ...config,
      evidence_templates: [...config.evidence_templates, newTemplate],
    });
  }

  function removeEvidenceTemplate(index: number) {
    if (!config) return;
    const newTemplates = config.evidence_templates.filter((_, i) => i !== index);
    setConfig({ ...config, evidence_templates: newTemplates });
  }

  if (loading && !config) {
    return (
      <div className="flex h-screen items-center justify-center bg-dossier-50">
        <p className="text-lg text-dossier-600">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dossier-50 p-6">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-dossier-800">Scenario Editor</h1>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md bg-dossier-200 px-4 py-2 text-sm font-medium text-dossier-800 hover:bg-dossier-300"
          >
            Back to Game
          </button>
        </div>

        {/* Error/Success Messages */}
        {error && (
          <div className="mb-4 rounded-md bg-red-100 border border-red-300 p-3 text-red-800">
            {error}
          </div>
        )}
        {successMessage && (
          <div className="mb-4 rounded-md bg-green-100 border border-green-300 p-3 text-green-800">
            {successMessage}
          </div>
        )}

        {/* Scenario Selector */}
        <div className="mb-6 rounded-lg bg-white p-4 shadow">
          <label className="mb-2 block text-sm font-medium text-dossier-700">
            Select Scenario
          </label>
          <select
            value={selectedScenario}
            onChange={(e) => handleScenarioChange(e.target.value)}
            className="w-full rounded-md border border-dossier-300 px-3 py-2"
          >
            {scenarios.map((scenario) => (
              <option key={scenario} value={scenario}>
                {scenario}
              </option>
            ))}
          </select>
        </div>

        {config && (
          <>
            {/* Basic Configuration */}
            <div className="mb-6 rounded-lg bg-white p-6 shadow">
              <h2 className="mb-4 text-xl font-semibold text-dossier-800">
                Basic Configuration
              </h2>

              <div className="mb-4">
                <label className="mb-1 block text-sm font-medium text-dossier-700">
                  Name
                </label>
                <input
                  type="text"
                  value={config.name}
                  onChange={(e) => updateConfig({ name: e.target.value })}
                  className="w-full rounded-md border border-dossier-300 px-3 py-2"
                />
              </div>

              <div className="mb-4">
                <label className="mb-1 block text-sm font-medium text-dossier-700">
                  Default Public Pressure
                </label>
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.01"
                  value={config.default_public_pressure}
                  onChange={(e) =>
                    updateConfig({ default_public_pressure: parseFloat(e.target.value) })
                  }
                  className="w-full rounded-md border border-dossier-300 px-3 py-2"
                />
              </div>

              <div className="mb-4">
                <label className="mb-1 block text-sm font-medium text-dossier-700">
                  Allowed Evidence Types
                </label>
                <div className="space-y-2">
                  {["physical", "digital", "testimonial", "circumstantial"].map((type) => (
                    <label key={type} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={config.allowed_evidence_types.includes(type)}
                        onChange={(e) => {
                          const types = e.target.checked
                            ? [...config.allowed_evidence_types, type]
                            : config.allowed_evidence_types.filter((t) => t !== type);
                          updateConfig({ allowed_evidence_types: types });
                        }}
                        className="mr-2"
                      />
                      {type}
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {/* Baseline Hypotheses */}
            <div className="mb-6 rounded-lg bg-white p-6 shadow">
              <h2 className="mb-4 text-xl font-semibold text-dossier-800">
                Baseline Hypotheses
              </h2>
              {Object.entries(config.baseline_hypotheses).map(([key, value]) => (
                <div key={key} className="mb-3">
                  <label className="mb-1 block text-sm font-medium text-dossier-700">
                    {key}
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={value}
                    onChange={(e) => updateHypothesis(key, parseFloat(e.target.value))}
                    className="w-full rounded-md border border-dossier-300 px-3 py-2"
                  />
                </div>
              ))}
            </div>

            {/* Evidence Templates */}
            <div className="mb-6 rounded-lg bg-white p-6 shadow">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-xl font-semibold text-dossier-800">
                  Evidence Templates
                </h2>
                <button
                  type="button"
                  onClick={addEvidenceTemplate}
                  className="rounded-md bg-accent-blue px-3 py-1 text-sm text-white hover:bg-blue-700"
                >
                  Add Template
                </button>
              </div>

              <div className="space-y-4">
                {config.evidence_templates.map((template, index) => (
                  <div key={index} className="rounded border border-dossier-200 p-4">
                    <div className="mb-2 flex items-center justify-between">
                      <h3 className="font-medium text-dossier-800">
                        Template {index + 1}: {template.id}
                      </h3>
                      <button
                        type="button"
                        onClick={() => removeEvidenceTemplate(index)}
                        className="text-sm text-red-600 hover:text-red-800"
                      >
                        Remove
                      </button>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="mb-1 block text-xs font-medium text-dossier-600">
                          ID
                        </label>
                        <input
                          type="text"
                          value={template.id}
                          onChange={(e) =>
                            updateEvidenceTemplate(index, { id: e.target.value })
                          }
                          className="w-full rounded border border-dossier-300 px-2 py-1 text-sm"
                        />
                      </div>

                      <div>
                        <label className="mb-1 block text-xs font-medium text-dossier-600">
                          Category
                        </label>
                        <select
                          value={template.category}
                          onChange={(e) =>
                            updateEvidenceTemplate(index, { category: e.target.value })
                          }
                          className="w-full rounded border border-dossier-300 px-2 py-1 text-sm"
                        >
                          <option value="physical">Physical</option>
                          <option value="digital">Digital</option>
                          <option value="testimonial">Testimonial</option>
                          <option value="circumstantial">Circumstantial</option>
                        </select>
                      </div>

                      <div>
                        <label className="mb-1 block text-xs font-medium text-dossier-600">
                          Base Reliability
                        </label>
                        <input
                          type="number"
                          min="0"
                          max="1"
                          step="0.01"
                          value={template.base_reliability}
                          onChange={(e) =>
                            updateEvidenceTemplate(index, {
                              base_reliability: parseFloat(e.target.value),
                            })
                          }
                          className="w-full rounded border border-dossier-300 px-2 py-1 text-sm"
                        />
                      </div>

                      <div>
                        <label className="mb-1 block text-xs font-medium text-dossier-600">
                          Detectability
                        </label>
                        <input
                          type="number"
                          min="0"
                          max="1"
                          step="0.01"
                          value={template.detectability}
                          onChange={(e) =>
                            updateEvidenceTemplate(index, {
                              detectability: parseFloat(e.target.value),
                            })
                          }
                          className="w-full rounded border border-dossier-300 px-2 py-1 text-sm"
                        />
                      </div>

                      <div>
                        <label className="mb-1 block text-xs font-medium text-dossier-600">
                          Manipulability
                        </label>
                        <input
                          type="number"
                          min="0"
                          max="1"
                          step="0.01"
                          value={template.manipulability}
                          onChange={(e) =>
                            updateEvidenceTemplate(index, {
                              manipulability: parseFloat(e.target.value),
                            })
                          }
                          className="w-full rounded border border-dossier-300 px-2 py-1 text-sm"
                        />
                      </div>

                      <div>
                        <label className="mb-1 block text-xs font-medium text-dossier-600">
                          Current Credibility
                        </label>
                        <input
                          type="number"
                          min="0"
                          max="1"
                          step="0.01"
                          value={template.current_credibility}
                          onChange={(e) =>
                            updateEvidenceTemplate(index, {
                              current_credibility: parseFloat(e.target.value),
                            })
                          }
                          className="w-full rounded border border-dossier-300 px-2 py-1 text-sm"
                        />
                      </div>
                    </div>

                    <div className="mt-3">
                      <label className="mb-1 block text-xs font-medium text-dossier-600">
                        Hypothesis Impacts (JSON)
                      </label>
                      <textarea
                        value={JSON.stringify(template.hypothesis_impacts, null, 2)}
                        onChange={(e) => {
                          try {
                            const impacts = JSON.parse(e.target.value);
                            updateEvidenceTemplate(index, { hypothesis_impacts: impacts });
                          } catch {
                            // Invalid JSON, ignore
                          }
                        }}
                        className="w-full rounded border border-dossier-300 px-2 py-1 text-sm font-mono"
                        rows={3}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleSave}
                disabled={saving}
                className="rounded-md bg-green-600 px-6 py-3 text-white hover:bg-green-700 disabled:bg-gray-400"
              >
                {saving ? "Saving..." : "Save Scenario"}
              </button>
              <button
                type="button"
                onClick={handlePlay}
                disabled={loading}
                className="rounded-md bg-accent-blue px-6 py-3 text-white hover:bg-blue-700 disabled:bg-gray-400"
              >
                {loading ? "Loading..." : "Play Scenario"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
