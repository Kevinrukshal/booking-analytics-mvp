import { Search, SlidersHorizontal, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { downloadFile, queryString } from "../api/client";
import { Badge, statusTone } from "../components/ui/Badge";
import { ExportToolbar } from "../components/ui/ExportToolbar";
import { EmptyDataset, ErrorState, LoadingState } from "../components/ui/PageStates";
import { PageHeader } from "../components/ui/PageHeader";
import { useApi } from "../hooks/useApi";
import type { Booking, Filters, Paginated } from "../types";
import { currency, date } from "../utils/format";

type ExportMode = "filtered" | "selected";

export function Bookings() {
  const [urlParams] = useSearchParams();
  const [search, setSearch] = useState("");
  const [agent, setAgent] = useState("");
  const [team, setTeam] = useState("");
  const [bookingStatus, setBookingStatus] = useState("");
  const [productStatus, setProductStatus] = useState("");
  const [hasErrors, setHasErrors] = useState(urlParams.get("hasErrors") || "");
  const [pendingProduct, setPendingProduct] = useState(urlParams.get("pendingProduct") || "");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [exporting, setExporting] = useState<ExportMode>();
  const [exportError, setExportError] = useState<string>();

  const filterParams = useMemo(() => queryString({
    search,
    agent,
    team,
    booking_status: bookingStatus,
    product_status: productStatus,
    hasErrors: hasErrors || undefined,
    pendingProduct: pendingProduct || undefined,
    dateFrom,
    dateTo,
  }), [search, agent, team, bookingStatus, productStatus, hasErrors, pendingProduct, dateFrom, dateTo]);
  const params = useMemo(() => `${filterParams}${filterParams ? "&" : ""}${queryString({ page, pageSize: 25 })}`, [filterParams, page]);
  const { data, loading, error, retry } = useApi<Paginated<Booking>>(`/api/bookings?${params}`);
  const filters = useApi<Filters>("/api/filters");

  useEffect(() => setSelected(new Set()), [filterParams]);

  const activeFilterCount = [search, agent, team, bookingStatus, productStatus, hasErrors, pendingProduct, dateFrom, dateTo].filter(Boolean).length;
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
    setSearch(""); setAgent(""); setTeam(""); setBookingStatus(""); setProductStatus("");
    setHasErrors(""); setPendingProduct(""); setDateFrom(""); setDateTo(""); setPage(1);
  }

  async function exportRows(mode: ExportMode) {
    setExporting(mode);
    setExportError(undefined);
    const query = new URLSearchParams(filterParams);
    if (mode === "selected") query.set("ids", [...selected].join(","));
    try {
      await downloadFile(`/api/bookings/export?${query}`, "booking-analytics-bookings.xlsx");
    } catch (cause) {
      setExportError(cause instanceof Error ? cause.message : "Could not export bookings.");
    } finally {
      setExporting(undefined);
    }
  }

  if (error) return <ErrorState message={error} retry={retry} />;
  return <>
    <PageHeader title="Bookings" description="Search, select and export the booking records your team needs." />

    <section className="card mb-5 p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-700"><SlidersHorizontal size={16} />Filters {activeFilterCount > 0 && <span className="rounded-full bg-accent-50 px-2 py-0.5 text-xs text-accent-700">{activeFilterCount} active</span>}</div>
        {activeFilterCount > 0 && <button className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500 hover:text-slate-800" onClick={resetFilters}><X size={14} />Reset</button>}
      </div>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <label className="relative md:col-span-2 xl:col-span-2"><Search size={16} className="absolute left-3 top-3 text-slate-400"/><input className="input w-full pl-9" value={search} onChange={(event) => update(setSearch, event.target.value)} placeholder="Booking ref, agent or team" /></label>
        <Select value={agent} onChange={(value) => update(setAgent, value)} label="All agents" values={filters.data?.agents}/>
        <Select value={team} onChange={(value) => update(setTeam, value)} label="All teams" values={filters.data?.teams}/>
        <Select value={bookingStatus} onChange={(value) => update(setBookingStatus, value)} label="All booking statuses" values={filters.data?.bookingStatuses}/>
        <Select value={productStatus} onChange={(value) => update(setProductStatus, value)} label="All product statuses" values={filters.data?.productStatuses}/>
        <select className="input" value={hasErrors} onChange={(event) => update(setHasErrors, event.target.value)}><option value="">Any error state</option><option value="true">Has errors</option><option value="false">No errors</option></select>
        <select className="input" value={pendingProduct} onChange={(event) => update(setPendingProduct, event.target.value)}><option value="">Any fulfilment state</option><option value="true">Pending products</option></select>
        <label className="relative"><span className="pointer-events-none absolute left-3 top-1 text-[9px] font-semibold uppercase tracking-wide text-slate-400">Travel from</span><input aria-label="Travel date from" className="input w-full pt-3" type="date" value={dateFrom} onChange={(event) => update(setDateFrom, event.target.value)} /></label>
        <label className="relative"><span className="pointer-events-none absolute left-3 top-1 text-[9px] font-semibold uppercase tracking-wide text-slate-400">Travel to</span><input aria-label="Travel date to" className="input w-full pt-3" type="date" value={dateTo} onChange={(event) => update(setDateTo, event.target.value)} /></label>
      </div>
    </section>

    {!loading && data && <ExportToolbar total={data.total} selectedCount={selected.size} exporting={exporting} onExport={(mode) => void exportRows(mode)} onClearSelection={() => setSelected(new Set())} />}
    {exportError && <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{exportError}</div>}

    {loading ? <LoadingState /> : !data?.items.length ? (data?.total === 0 && activeFilterCount === 0 ? <EmptyDataset /> : <div className="card p-12 text-center text-sm text-slate-500">No bookings match these filters.</div>) : <>
      <div className="table-wrap"><table className="data-table"><thead><tr>
        <th className="w-12"><input aria-label="Select all bookings on this page" className="checkbox" type="checkbox" checked={allVisibleSelected} ref={(input) => { if (input) input.indeterminate = someVisibleSelected; }} onChange={toggleVisible}/></th>
        <th>Booking ref</th><th>Agent</th><th>Team</th><th>Travel date</th><th>Booking status</th><th>Product status</th><th>Errors</th><th>Open</th><th>Selling value</th><th>Profit</th>
      </tr></thead><tbody>{data.items.map((row) => <tr key={row.id} className={`transition hover:bg-slate-50/70 ${selected.has(row.id) ? "bg-accent-50/60" : ""}`}>
        <td><input aria-label={`Select booking ${row.bookingReference}`} className="checkbox" type="checkbox" checked={selected.has(row.id)} onChange={() => toggleRow(row.id)}/></td>
        <td><Link className="font-semibold text-accent-700 hover:underline" to={`/bookings/${row.bookingReference}`}>{row.bookingReference}</Link></td><td>{row.agent || "—"}</td><td>{row.team || "—"}</td><td className="whitespace-nowrap">{date(row.travelDate)}</td><td><Badge tone={statusTone(row.bookingStatus)}>{row.bookingStatus || "Unknown"}</Badge></td><td><Badge tone={statusTone(row.productStatus)}>{row.productStatus || "Unknown"}</Badge></td><td>{row.errorCount}</td><td className={row.openErrorCount ? "font-semibold text-red-600" : "text-slate-400"}>{row.openErrorCount}</td><td className="whitespace-nowrap">{currency(row.sellingCost)}</td><td className="whitespace-nowrap font-medium">{currency(row.profit)}</td>
      </tr>)}</tbody></table></div>
      <Pagination page={page} total={data.total} pageSize={data.pageSize} setPage={setPage}/>
    </>}
  </>;
}

function Select({ value, onChange, label, values }: { value: string; onChange: (value: string) => void; label: string; values?: string[] }) {
  return <select className="input" value={value} onChange={(event) => onChange(event.target.value)}><option value="">{label}</option>{values?.map((item) => <option key={item}>{item}</option>)}</select>;
}

export function Pagination({ page, total, pageSize, setPage }: { page: number; total: number; pageSize: number; setPage: (page: number) => void }) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return <div className="mt-4 flex items-center justify-between text-sm text-slate-500"><span>{total.toLocaleString()} records</span><div className="flex items-center gap-2"><button className="button-secondary h-9" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button><span className="px-2">{page} / {pages}</span><button className="button-secondary h-9" disabled={page >= pages} onClick={() => setPage(page + 1)}>Next</button></div></div>;
}
