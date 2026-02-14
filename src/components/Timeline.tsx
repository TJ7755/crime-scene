import type { TimelineItem } from "../api/engineAdapter";

interface TimelineProps {
  entries: TimelineItem[];
  selectedIndex: number;
  onSelect: (index: number) => void;
}

function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short",
  });
}

/** Displays timeline entries for quick event navigation in the left panel. */
export function Timeline({ entries, selectedIndex, onSelect }: TimelineProps) {
  if (entries.length === 0) {
    return <p className="text-sm text-dossier-500">No timeline entries available.</p>;
  }

  return (
    <ol className="space-y-2" aria-label="Case timeline">
      {entries.map((entry, index) => {
        const isSelected = index === selectedIndex;
        return (
          <li key={`${entry.time}-${entry.label}-${index}`}>
            <button
              type="button"
              onClick={() => onSelect(index)}
              aria-pressed={isSelected}
              className={`w-full rounded-sm border px-2 py-2 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-blue ${
                isSelected
                  ? "border-accent-blue bg-dossier-100/80"
                  : "border-dossier-200 bg-white/80 hover:bg-dossier-50"
              }`}
            >
              <p className="dossier-label">{formatTimestamp(entry.time)}</p>
              <p className="mt-1 text-sm font-semibold text-dossier-900">{entry.label}</p>
              <p className="mt-1 text-xs text-dossier-600">{entry.details}</p>
            </button>
          </li>
        );
      })}
    </ol>
  );
}
