import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { queryString } from "../api/client";
import { Badge, statusTone } from "../components/ui/Badge";
import { EmptyDataset, ErrorState, LoadingState } from "../components/ui/PageStates";
import { PageHeader } from "../components/ui/PageHeader";
import { useApi } from "../hooks/useApi";
import type { Booking, Filters, Paginated } from "../types";
import { currency, date } from "../utils/format";

export function Bookings() {
  const [urlParams] = useSearchParams();
  const [search, setSearch] = useState(""); const [agent, setAgent] = useState(""); const [team, setTeam] = useState("");
  const [productStatus, setProductStatus] = useState(""); const [hasErrors, setHasErrors] = useState(urlParams.get("hasErrors") || "");
  const [pendingProduct, setPendingProduct] = useState(urlParams.get("pendingProduct") || ""); const [page, setPage] = useState(1);
  const params = useMemo(() => queryString({ search, agent, team, product_status: productStatus, hasErrors: hasErrors || undefined, pendingProduct: pendingProduct || undefined, page, pageSize: 25 }), [search, agent, team, productStatus, hasErrors, pendingProduct, page]);
  const { data, loading, error, retry } = useApi<Paginated<Booking>>(`/api/bookings?${params}`);
  const filters = useApi<Filters>("/api/filters");
  if (error) return <ErrorState message={error} retry={retry} />;
  return <><PageHeader title="Bookings" description="Search the latest booking sheet and find records requiring action." />
    <div className="card mb-5 grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-6"><label className="relative md:col-span-2 xl:col-span-2"><Search size={16} className="absolute left-3 top-3 text-slate-400"/><input className="input w-full pl-9" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} placeholder="Booking ref, agent or team" /></label><Select value={agent} setValue={setAgent} label="All agents" values={filters.data?.agents}/><Select value={team} setValue={setTeam} label="All teams" values={filters.data?.teams}/><Select value={productStatus} setValue={setProductStatus} label="All product statuses" values={filters.data?.productStatuses}/><select className="input" value={hasErrors} onChange={(event) => { setHasErrors(event.target.value); setPage(1); }}><option value="">Any error state</option><option value="true">Has errors</option><option value="false">No errors</option></select><select className="input" value={pendingProduct} onChange={(event) => { setPendingProduct(event.target.value); setPage(1); }}><option value="">Any fulfilment state</option><option value="true">Pending products</option></select></div>
    {loading ? <LoadingState /> : !data?.items.length ? (data?.total === 0 && !search && !agent && !team && !productStatus && !hasErrors && !pendingProduct ? <EmptyDataset /> : <div className="card p-12 text-center text-sm text-slate-500">No bookings match these filters.</div>) : <><div className="table-wrap"><table className="data-table"><thead><tr><th>Booking ref</th><th>Agent</th><th>Team</th><th>Travel date</th><th>Booking status</th><th>Product status</th><th>Errors</th><th>Open</th><th>Selling value</th><th>Profit</th></tr></thead><tbody>{data.items.map((row) => <tr key={row.id} className="transition hover:bg-slate-50/70"><td><Link className="font-semibold text-accent-700 hover:underline" to={`/bookings/${row.bookingReference}`}>{row.bookingReference}</Link></td><td>{row.agent || "—"}</td><td>{row.team || "—"}</td><td className="whitespace-nowrap">{date(row.travelDate)}</td><td><Badge tone={statusTone(row.bookingStatus)}>{row.bookingStatus || "Unknown"}</Badge></td><td><Badge tone={statusTone(row.productStatus)}>{row.productStatus || "Unknown"}</Badge></td><td>{row.errorCount}</td><td className={row.openErrorCount ? "font-semibold text-red-600" : "text-slate-400"}>{row.openErrorCount}</td><td className="whitespace-nowrap">{currency(row.sellingCost)}</td><td className="whitespace-nowrap font-medium">{currency(row.profit)}</td></tr>)}</tbody></table></div><Pagination page={page} total={data.total} pageSize={data.pageSize} setPage={setPage}/></>}
  </>;
}

function Select({ value, setValue, label, values }: { value: string; setValue: (value: string) => void; label: string; values?: string[] }) { return <select className="input" value={value} onChange={(event) => setValue(event.target.value)}><option value="">{label}</option>{values?.map((item) => <option key={item}>{item}</option>)}</select>; }
export function Pagination({ page, total, pageSize, setPage }: { page: number; total: number; pageSize: number; setPage: (page: number) => void }) { const pages = Math.max(1, Math.ceil(total / pageSize)); return <div className="mt-4 flex items-center justify-between text-sm text-slate-500"><span>{total.toLocaleString()} records</span><div className="flex items-center gap-2"><button className="button-secondary h-9" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button><span className="px-2">{page} / {pages}</span><button className="button-secondary h-9" disabled={page >= pages} onClick={() => setPage(page + 1)}>Next</button></div></div>; }

