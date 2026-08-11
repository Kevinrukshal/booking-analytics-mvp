import { ChevronDown, ChevronUp, Search, SlidersHorizontal, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { downloadFile, queryString } from "../api/client";
import { Badge, statusTone } from "../components/ui/Badge";
import { ExportToolbar } from "../components/ui/ExportToolbar";
import { EmptyDataset, ErrorState, LoadingState } from "../components/ui/PageStates";
import { PageHeader } from "../components/ui/PageHeader";
import { useApi } from "../hooks/useApi";
import type { ErrorRecord, Filters, Paginated } from "../types";
import { date } from "../utils/format";
import { Pagination } from "./Bookings";

type ExportMode = "filtered" | "selected";

export function Errors() {
  const [urlParams] = useSearchParams();
  const [reference, setReference] = useState("");
  const [status, setStatus] = useState(urlParams.get("status") || "");
  const [agent, setAgent] = useState("");
  const [handled, setHandled] = useState("");
  const [category, setCategory] = useState(urlParams.get("category") || "");
  const [severity, setSeverity] = useState("");
  const [matched, setMatched] = useState(urlParams.get("matched") || "");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [page, setPage] = useState(1);
  const [expanded, setExpanded] = useState<number>();
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [exporting, setExporting] = useState<ExportMode>();
  const [exportError, setExportError] = useState<string>();

  const filterParams = useMemo(() => queryString({
    bookingReference: reference,
    status,
    agent,
    handledAgent: handled,
    category,
    severity,
    matched: matched || undefined,
    dateFrom,
    dateTo,
  }), [reference, status, agent, handled, category, severity, matched, dateFrom, dateTo]);
  const params = useMemo(() => `${filterParams}${filterParams ? "&" : ""}${queryString({ page, pageSize: 25 })}`, [filterParams, page]);
  const { data, loading, error, retry } = useApi<Paginated<ErrorRecord>>(`/api/errors?${params}`);
  const filters = useApi<Filters>("/api/filters");

  useEffect(() => setSelected(new Set()), [filterParams]);

  const activeFilterCount = [reference, status, agent, handled, category, severity, matched, dateFrom, dateTo].filter(Boolean).length;
  const visibleIds = data?.items.map((row) => row.id) || [];
  const allVisibleSelected = visibleIds.length > 0 && visibleIds.every((id) => selected.has(id));
  const someVisibleSelected = visibleIds.some((id) => selected.has(id)) && !allVisibleSelected;

  function update(setter: (value: string) => void, value: string) {
    setter(value);
    setPage(1);
  }

  function toggleRow(id: number) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }

  function toggleVisible() {
    setSelected((current) => {
      const next = new Set(current);
      visibleIds.forEach((id) => allVisibleSelected ? next.delete(id) : next.add(id));
      return next;
    });
  }

  function resetFilters() {
    setReference(""); setStatus(""); setAgent(""); setHandled(""); setCategory("");
    setSeverity(""); setMatched(""); setDateFrom(""); setDateTo(""); setPage(1);
  }

  async function exportRows(mode: ExportMode) {
    setExporting(mode);
    setExportError(undefined);
    const query = new URLSearchParams(filterParams);
    if (mode === "selected") query.set("ids", [...selected].join(","));
    try {
      await downloadFile(`/api/errors/export?${query}`, "booking-analytics-errors.xlsx");
    } catch (cause) {
      setExportError(cause instanceof Error ? cause.message : "Could not export errors.");
    } finally {
      setExporting(undefined);
    }
  }

  if (error) return <ErrorState message={error} retry={retry}/>;
  return <>
    <PageHeader title="Errors" description="Review, filter and export booking-quality issues."/>

    <section className="card mb-5 p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-700"><SlidersHorizontal size={16}/>Filters {activeFilterCount > 0 && <span className="rounded-full bg-accent-50 px-2 py-0.5 text-xs text-accent-700">{activeFilterCount} active</span>}</div>
        {activeFilterCount > 0 && <button className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500 hover:text-slate-800" onClick={resetFilters}><X size={14}/>Reset</button>}
      </div>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <label className="relative md:col-span-2"><Search size={16} className="absolute left-3 top-3 text-slate-400"/><input className="input w-full pl-9" placeholder="Booking reference" value={reference} onChange={(event) => update(setReference, event.target.value)}/></label>
        <Select value={status} onChange={(value) => update(setStatus, value)} label="All statuses" values={["open", "pending", "resolved"]}/>
        <Select value={agent} onChange={(value) => update(setAgent, value)} label="All agents" values={filters.data?.agents}/>
        <Select value={handled} onChange={(value) => update(setHandled, value)} label="All handlers" values={filters.data?.handledAgents}/>
        <Select value={category} onChange={(value) => update(setCategory, value)} label="All categories" values={filters.data?.categories}/>
        <Select value={severity} onChange={(value) => update(setSeverity, value)} label="All severities" values={filters.data?.severities}/>
        <Select value={matched} onChange={(value) => update(setMatched, value)} label="All join states" values={["true", "false"]} labels={{ true: "Matches current booking", false: "Historical / unmatched" }}/>
        <label className="relative"><span className="pointer-events-none absolute left-3 top-1 text-[9px] font-semibold uppercase tracking-wide text-slate-400">Issue from</span><input aria-label="Issue date from" className="input w-full pt-3" type="date" value={dateFrom} onChange={(event) => update(setDateFrom, event.target.value)}/></label>
        <label className="relative"><span className="pointer-events-none absolute left-3 top-1 text-[9px] font-semibold uppercase tracking-wide text-slate-400">Issue to</span><input aria-label="Issue date to" className="input w-full pt-3" type="date" value={dateTo} onChange={(event) => update(setDateTo, event.target.value)}/></label>
      </div>
    </section>

    {!loading && data && <ExportToolbar total={data.total} selectedCount={selected.size} exporting={exporting} onExport={(mode) => void exportRows(mode)} onClearSelection={() => setSelected(new Set())}/>}
    {exportError && <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{exportError}</div>}

    {loading ? <LoadingState/> : !data?.items.length ? (activeFilterCount ? <div className="card p-12 text-center text-sm text-slate-500">No errors match these filters.</div> : <EmptyDataset/>) : <>
      <div className="table-wrap"><table className="data-table"><thead><tr>
        <th className="w-12"><input aria-label="Select all errors on this page" className="checkbox" type="checkbox" checked={allVisibleSelected} ref={(input) => { if (input) input.indeterminate = someVisibleSelected; }} onChange={toggleVisible}/></th>
        <th>Booking ref</th><th>Agent</th><th>Issue</th><th>Category</th><th>Severity</th><th>Status</th><th>Handled by</th><th>Date</th><th></th>
      </tr></thead><tbody>{data.items.map((item) => <ErrorRow key={item.id} item={item} selected={selected.has(item.id)} toggleSelected={() => toggleRow(item.id)} open={expanded === item.id} toggle={() => setExpanded(expanded === item.id ? undefined : item.id)}/>)}</tbody></table></div>
      <Pagination page={page} total={data.total} pageSize={data.pageSize} setPage={setPage}/>
    </>}
  </>;
}

function ErrorRow({ item, selected, toggleSelected, open, toggle }: { item: ErrorRecord; selected: boolean; toggleSelected: () => void; open: boolean; toggle: () => void }) {
  return <>
    <tr className={`hover:bg-slate-50/70 ${selected ? "bg-accent-50/60" : ""}`}>
      <td><input aria-label={`Select error ${item.id}`} className="checkbox" type="checkbox" checked={selected} onChange={toggleSelected}/></td>
      <td>{item.matched ? <Link className="font-semibold text-accent-700" to={`/bookings/${item.bookingReference}`}>{item.bookingReference}</Link> : <span className="font-medium">{item.bookingReference}</span>}</td><td>{item.responsibleAgent || "—"}</td><td className="max-w-sm"><p className="truncate">{item.issueText}</p>{item.matched === false && <span className="mt-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-400">Historical / unmatched</span>}</td><td><Badge>{item.category}</Badge></td><td><Badge tone={statusTone(item.severity)}>{item.severity}</Badge></td><td><Badge tone={statusTone(item.status)}>{item.status}</Badge></td><td>{item.handledAgent || "—"}</td><td className="whitespace-nowrap">{date(item.issueDate)}</td><td><button aria-label={open ? "Collapse error details" : "Expand error details"} className="rounded-lg p-2 text-slate-400 hover:bg-slate-100" onClick={toggle}>{open ? <ChevronUp size={16}/> : <ChevronDown size={16}/>}</button></td>
    </tr>
    {open && <tr><td colSpan={10} className="!bg-slate-50/70"><div className="grid gap-5 p-3 lg:grid-cols-3"><div className="lg:col-span-2"><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Full issue</p><p className="mt-2 text-sm leading-6 text-slate-700">{item.issueText}</p></div><div><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Remarks</p><p className="mt-2 text-sm leading-6 text-slate-600">{item.remarks || "No remarks recorded."}</p></div><div><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Action taken</p><p className="mt-2 text-sm leading-6 text-slate-600">{item.actionTaken || "No action recorded."}</p></div></div></td></tr>}
  </>;
}

function Select({ value, onChange, label, values, labels }: { value: string; onChange: (value: string) => void; label: string; values?: string[]; labels?: Record<string, string> }) {
  return <select className="input" value={value} onChange={(event) => onChange(event.target.value)}><option value="">{label}</option>{values?.map((item) => <option value={item} key={item}>{labels?.[item] || item}</option>)}</select>;
}
