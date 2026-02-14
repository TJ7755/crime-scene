import type { PressureState } from "../api/engineAdapter";

interface PressurePanelProps {
  pressure: PressureState;
}

function formatToken(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

/** Shows qualitative pressure indicators in the right-side panel. */
export function PressurePanel({ pressure }: PressurePanelProps) {
  return (
    <section className="dossier-panel" aria-label="Pressure and atmosphere">
      <h2 className="dossier-label">Pressure & Atmosphere</h2>
      <dl className="mt-3 space-y-3">
        <div className="rounded-sm border border-dossier-200 bg-white/80 p-2">
          <dt className="text-xs text-dossier-500">Public</dt>
          <dd className="mt-1 text-sm font-semibold text-dossier-900">{formatToken(pressure.public)}</dd>
        </div>
        <div className="rounded-sm border border-dossier-200 bg-white/80 p-2">
          <dt className="text-xs text-dossier-500">Institutional</dt>
          <dd className="mt-1 text-sm font-semibold text-dossier-900">
            {formatToken(pressure.institutional)}
          </dd>
        </div>
        <div className="rounded-sm border border-dossier-200 bg-white/80 p-2">
          <dt className="text-xs text-dossier-500">Personal</dt>
          <dd className="mt-1 text-sm font-semibold text-dossier-900">
            {formatToken(pressure.personal)}
          </dd>
        </div>
      </dl>
    </section>
  );
}
