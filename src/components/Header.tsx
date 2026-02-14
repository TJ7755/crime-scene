interface HeaderProps {
  caseId: string;
  crimeType: string;
  day: number;
  status: string;
  activePage: string;
  pages: string[];
  adapterKind: "live" | "mock";
  busy: boolean;
  onPageChange: (page: string) => void;
  onSavePage: () => void;
  onLoadPage: () => void;
}

function formatToken(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

/** Renders the top case metadata band and case page save/load controls. */
export function Header({
  caseId,
  crimeType,
  day,
  status,
  activePage,
  pages,
  adapterKind,
  busy,
  onPageChange,
  onSavePage,
  onLoadPage,
}: HeaderProps) {
  return (
    <header className="dossier-panel mb-3" role="banner" aria-label="Case header">
      <h1 className="sr-only">Case dossier interface</h1>
      <div className="grid gap-3 md:grid-cols-[repeat(4,minmax(0,1fr))_auto]">
        <section>
          <p className="dossier-label">Case ID</p>
          <p className="mt-1 font-semibold tracking-wide text-dossier-900">{caseId}</p>
        </section>
        <section>
          <p className="dossier-label">Crime Type</p>
          <p className="mt-1 font-semibold tracking-wide text-dossier-900">
            {formatToken(crimeType)}
          </p>
        </section>
        <section>
          <p className="dossier-label">Day</p>
          <p className="mt-1 font-semibold tracking-wide text-dossier-900">Day {day}</p>
        </section>
        <section>
          <p className="dossier-label">Status</p>
          <p className="mt-1 font-semibold tracking-wide text-dossier-900">{formatToken(status)}</p>
        </section>

        <section className="rounded-sm border border-dossier-200 bg-dossier-50/70 p-2">
          <p className="dossier-label">Case Page</p>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <label className="sr-only" htmlFor="case-page-select">
              Select case page
            </label>
            <select
              id="case-page-select"
              className="rounded-sm border border-dossier-300 bg-white px-2 py-1 text-sm text-dossier-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-blue"
              value={activePage}
              onChange={(event) => onPageChange(event.target.value)}
              disabled={busy}
            >
              {pages.map((page) => (
                <option key={page} value={page}>
                  {formatToken(page)}
                </option>
              ))}
            </select>
            <button
              type="button"
              className="rounded-sm border border-dossier-300 bg-white px-2 py-1 text-sm text-dossier-800 transition-colors hover:bg-dossier-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-blue disabled:cursor-not-allowed disabled:opacity-60"
              onClick={onSavePage}
              disabled={busy}
            >
              Save
            </button>
            <button
              type="button"
              className="rounded-sm border border-dossier-300 bg-white px-2 py-1 text-sm text-dossier-800 transition-colors hover:bg-dossier-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-blue disabled:cursor-not-allowed disabled:opacity-60"
              onClick={onLoadPage}
              disabled={busy}
            >
              Load
            </button>
          </div>
          <p className="mt-2 text-xs text-dossier-500">Adapter: {adapterKind.toUpperCase()}</p>
        </section>
      </div>
    </header>
  );
}
