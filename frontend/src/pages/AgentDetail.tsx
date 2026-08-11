import { ArrowLeft } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Link, useParams } from "react-router-dom";
import { ChartCard } from "../components/charts/ChartCard";
import { MetricCard } from "../components/dashboard/MetricCard";
import { Badge, statusTone } from "../components/ui/Badge";
import { ErrorState, LoadingState } from "../components/ui/PageStates";
import { useApi } from "../hooks/useApi";
import type { AgentMetric, Booking } from "../types";
import { currency, date, percent } from "../utils/format";
import { BookOpen, CircleDollarSign, Clock3, ShieldAlert } from "lucide-react";

type Detail = { agent: AgentMetric; errorBreakdown: { category: string; value: number }[]; bookings: Booking[] };

export function AgentDetail() {
  const { agent = "" } = useParams(); const { data, loading, error, retry } = useApi<Detail>(`/api/agents/${encodeURIComponent(agent)}`);
  if (loading) return <LoadingState rows={6}/>; if (error || !data) return <ErrorState message={error || "Agent not found."} retry={retry}/>;
  return <><Link to="/agents" className="mb-6 inline-flex items-center gap-2 text-sm font-medium text-slate-500"><ArrowLeft size={16}/>Back to agents</Link><div className="mb-7 flex items-end justify-between"><div><h1 className="text-3xl font-bold">{data.agent.agent}</h1><p className="mt-1 text-sm text-slate-500">{data.agent.team}</p></div><Badge tone={statusTone(data.agent.status)}>{data.agent.status}</Badge></div><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><MetricCard label="Bookings" value={String(data.agent.bookings)} context="Current workbook" icon={BookOpen}/><MetricCard label="Error rate" value={percent(data.agent.errorRate)} context={`${data.agent.errorBookings} error bookings`} icon={ShieldAlert}/><MetricCard label="Open errors" value={String(data.agent.openErrors)} context="Unresolved records" icon={Clock3}/><MetricCard label="Profit" value={currency(data.agent.profit)} context="Latest normalized rows" icon={CircleDollarSign}/></div><div className="mt-6"><ChartCard title="Error breakdown" description="Errors associated with this agent's current bookings">{data.errorBreakdown.length ? <ResponsiveContainer width="100%" height="100%"><BarChart data={data.errorBreakdown} layout="vertical" margin={{ left: 45 }}><CartesianGrid horizontal={false} stroke="#eef1f0"/><XAxis type="number" allowDecimals={false}/><YAxis type="category" dataKey="category" width={120} tick={{ fontSize: 11 }}/><Tooltip/><Bar dataKey="value" fill="#16846b" radius={[0, 5, 5, 0]} maxBarSize={18}/></BarChart></ResponsiveContainer> : <div className="grid h-full place-items-center text-sm text-slate-400">No matched errors</div>}</ChartCard></div><section className="mt-6"><h2 className="mb-3 text-lg font-semibold">Recent and problem bookings</h2><div className="table-wrap"><table className="data-table"><thead><tr><th>Booking ref</th><th>Travel date</th><th>Status</th><th>Errors</th><th>Open</th><th>Pending product</th><th>Profit</th></tr></thead><tbody>{data.bookings.map((row) => <tr key={row.id}><td><Link className="font-semibold text-accent-700" to={`/bookings/${row.bookingReference}`}>{row.bookingReference}</Link></td><td>{date(row.travelDate)}</td><td><Badge tone={statusTone(row.productStatus)}>{row.productStatus || "Unknown"}</Badge></td><td>{row.errorCount}</td><td>{row.openErrorCount}</td><td className="max-w-xs truncate">{row.pendingProducts || "—"}</td><td>{currency(row.profit)}</td></tr>)}</tbody></table></div></section></>;
}

