import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { queryString } from "../api/client";
import { Badge, statusTone } from "../components/ui/Badge";
import { EmptyDataset, ErrorState, LoadingState } from "../components/ui/PageStates";
import { PageHeader } from "../components/ui/PageHeader";
import { useApi } from "../hooks/useApi";
import type { AgentMetric, Filters } from "../types";
import { currency, percent } from "../utils/format";

type AgentResponse = { items: AgentMetric[]; overallErrorRate: number; minimumRankingBookings: number };

export function Agents() {
  const [search, setSearch] = useState(""); const [team, setTeam] = useState(""); const [minimum, setMinimum] = useState(0);
  const params = useMemo(() => queryString({ search, team, minBookings: minimum }), [search, team, minimum]);
  const { data, loading, error, retry } = useApi<AgentResponse>(`/api/agents?${params}`); const filters = useApi<Filters>("/api/filters");
  if (error) return <ErrorState message={error} retry={retry}/>;
  return <><PageHeader title="Agents" description="Compare workload, quality and unresolved issues." actions={data && <div className="text-right"><p className="text-xs text-slate-400">Overall error rate</p><p className="font-semibold">{percent(data.overallErrorRate)}</p></div>}/><div className="card mb-5 grid gap-3 p-4 sm:grid-cols-3"><label className="relative"><Search size={16} className="absolute left-3 top-3 text-slate-400"/><input className="input w-full pl-9" placeholder="Search agent" value={search} onChange={(event) => setSearch(event.target.value)}/></label><select className="input" value={team} onChange={(event) => setTeam(event.target.value)}><option value="">All teams</option>{filters.data?.teams?.map((item) => <option key={item}>{item}</option>)}</select><label className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-3 text-xs text-slate-500">Minimum bookings<input type="number" min="0" className="w-full text-right text-sm font-medium text-slate-700" value={minimum} onChange={(event) => setMinimum(Number(event.target.value))}/></label></div>{loading ? <LoadingState/> : !data?.items.length ? <EmptyDataset/> : <><div className="mb-3 rounded-xl bg-slate-100 px-4 py-3 text-xs text-slate-500">Status thresholds: Healthy below overall average; Watch up to 1.5× average; Needs Attention above 1.5×. Rankings require {data.minimumRankingBookings} bookings.</div><div className="table-wrap"><table className="data-table"><thead><tr><th>Agent</th><th>Team</th><th>Bookings</th><th>Error bookings</th><th>Error rate</th><th>Open errors</th><th>Profit</th><th>Status</th></tr></thead><tbody>{data.items.map((item) => <tr key={item.agent} className="hover:bg-slate-50/70"><td><Link className="font-semibold text-accent-700 hover:underline" to={`/agents/${encodeURIComponent(item.agent)}`}>{item.agent}</Link></td><td>{item.team}</td><td>{item.bookings}</td><td>{item.errorBookings}</td><td className="font-medium">{percent(item.errorRate)}</td><td className={item.openErrors ? "font-semibold text-red-600" : "text-slate-400"}>{item.openErrors}</td><td>{currency(item.profit)}</td><td><Badge tone={statusTone(item.status)}>{item.status}</Badge></td></tr>)}</tbody></table></div></>}</>;
}

