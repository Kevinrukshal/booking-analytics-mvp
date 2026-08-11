import { CheckSquare2, Download, LoaderCircle } from "lucide-react";

type ExportMode = "filtered" | "selected";

export function ExportToolbar({
  total,
  selectedCount,
  exporting,
  onExport,
  onClearSelection,
}: {
  total: number;
  selectedCount: number;
  exporting?: ExportMode;
  onExport: (mode: ExportMode) => void;
  onClearSelection: () => void;
}) {
  return <div className="mb-4 flex flex-col gap-3 rounded-2xl border border-slate-200/80 bg-white px-4 py-3 shadow-card sm:flex-row sm:items-center sm:justify-between">
    <div>
      <p className="text-sm font-semibold text-slate-800">{total.toLocaleString()} matching record{total === 1 ? "" : "s"}</p>
      <p className="mt-0.5 text-xs text-slate-500">Export every filtered result, or tick specific rows below.</p>
    </div>
    <div className="flex flex-wrap items-center gap-2">
      {selectedCount > 0 && <button className="px-2 text-xs font-semibold text-slate-500 hover:text-slate-800" onClick={onClearSelection}>Clear selection</button>}
      <button className="button-secondary" disabled={!total || Boolean(exporting)} onClick={() => onExport("filtered")}>
        {exporting === "filtered" ? <LoaderCircle className="animate-spin" size={16} /> : <Download size={16} />}
        Export filtered <span className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[11px]">{total.toLocaleString()}</span>
      </button>
      <button className="button" disabled={!selectedCount || Boolean(exporting)} onClick={() => onExport("selected")}>
        {exporting === "selected" ? <LoaderCircle className="animate-spin" size={16} /> : <CheckSquare2 size={16} />}
        Export selected <span className="rounded-md bg-white/15 px-1.5 py-0.5 text-[11px]">{selectedCount}</span>
      </button>
    </div>
  </div>;
}
