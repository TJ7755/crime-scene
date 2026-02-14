import type { EvidenceItem } from "../api/engineAdapter";

interface EvidenceListProps {
  evidence: EvidenceItem[];
  selectedId: string | null;
  onSelect: (evidenceId: string) => void;
}

function categoryIcon(category: string) {
  switch (category) {
    case "digital":
      return (
        <svg viewBox="0 0 20 20" className="h-4 w-4" aria-hidden="true">
          <rect x="3" y="4" width="14" height="10" rx="1.5" fill="currentColor" />
          <rect x="8" y="15" width="4" height="1.5" rx="0.75" fill="currentColor" />
        </svg>
      );
    case "forensic":
      return (
        <svg viewBox="0 0 20 20" className="h-4 w-4" aria-hidden="true">
          <circle cx="10" cy="7" r="4" fill="currentColor" />
          <rect x="8.8" y="11" width="2.4" height="6" rx="1.2" fill="currentColor" />
        </svg>
      );
    case "document":
      return (
        <svg viewBox="0 0 20 20" className="h-4 w-4" aria-hidden="true">
          <path d="M5 2h7l3 3v13H5V2z" fill="currentColor" />
        </svg>
      );
    case "witness":
      return (
        <svg viewBox="0 0 20 20" className="h-4 w-4" aria-hidden="true">
          <circle cx="10" cy="6" r="3.5" fill="currentColor" />
          <rect x="5.2" y="10.8" width="9.6" height="6.5" rx="3.2" fill="currentColor" />
        </svg>
      );
    default:
      return (
        <svg viewBox="0 0 20 20" className="h-4 w-4" aria-hidden="true">
          <path d="M10 2l8 4v8l-8 4-8-4V6l8-4z" fill="currentColor" />
        </svg>
      );
  }
}

function formatToken(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

/** Shows all visible evidence items with category icon and discovery state badge. */
export function EvidenceList({ evidence, selectedId, onSelect }: EvidenceListProps) {
  if (evidence.length === 0) {
    return <p className="text-sm text-dossier-500">No evidence currently visible.</p>;
  }

  return (
    <ul className="space-y-2" aria-label="Visible evidence list">
      {evidence.map((item) => {
        const isSelected = item.id === selectedId;
        return (
          <li key={item.id}>
            <button
              type="button"
              onClick={() => onSelect(item.id)}
              aria-pressed={isSelected}
              className={`w-full rounded-sm border px-2 py-2 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-blue ${
                isSelected
                  ? "border-accent-blue bg-dossier-100/90"
                  : "border-dossier-200 bg-white/80 hover:bg-dossier-50"
              }`}
            >
              <span className="flex items-center gap-2">
                <span className="inline-flex h-6 w-6 items-center justify-center rounded-sm bg-dossier-200/80 text-dossier-700">
                  {categoryIcon(item.category)}
                  <span className="sr-only">{formatToken(item.category)} evidence icon</span>
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-medium text-dossier-900">
                    {item.label}
                  </span>
                </span>
                <span className="state-pill">{formatToken(item.state)}</span>
              </span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}
