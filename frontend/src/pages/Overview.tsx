import { AlertTriangle, BookOpen, CircleDollarSign, Clock3, PackageOpen, ShieldAlert } from "lucide-react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Link } from "react-router-dom";
import { ChartCard } from "../components/charts/ChartCard";
import { MetricCard } from "../components/dashboard/MetricCard";
import { EmptyDataset, ErrorState, LoadingState } from "../components/ui/PageStates";
import { PageHeader } from "../components/ui/PageHeader";
import { useApi } from "../hooks/useApi";
import type { Dashboard } from "../types";
import { compact, currency, percent } from "../utils/format";

const pieColors = ["#16846b", "#eab308", "#dc2626", "#94a3b8"];

export function Overview() {
  const { data, loading, error, retry } = useApi<Dashboard>("/api/dashboard");
  if (loading) return <><PageHeader title="Overview" description="Your booking operation at a glance." /><LoadingState rows={6} /></>;
  if (error) return <ErrorState message={error} retry={retry} />;
  if (!data || data.empty || !data.kpis) return <><PageHeader title="Overview" description="Your booking operation at a glance." /><EmptyDataset /></>;
  const k = data.kpis;
  const agentData = (data.agentPerformance || []).map((item) => ({ ...item, agentLabel: `${item.agent} (${item.bookings})`, errorRatePct: Number((item.errorRate * 100).toFixed(1)) }));
  return <>
    <PageHeader title="Overview" description={`A focused view of ${data.upload?.filename || "your latest workbook"}.`} actions={<Link className="button-secondary" to="/upload">Replace workbook</Link>} />
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
      <MetricCard label="Total bookings" value={k.totalBookings.toLocaleString()} context="Unique booking references" icon={BookOpen} />
      <MetricCard label="Bookings with errors" value={k.bookingsWithErrors.toLocaleString()} context={`${k.matchedErrors} matched error records`} icon={ShieldAlert} />
      <MetricCard label="Error rate" value={percent(k.errorRate)} context={`${k.bookingsWithErrors} of ${k.totalBookings} bookings`} icon={AlertTriangle} />
      <MetricCard label="Open errors" value={k.openErrors.toLocaleString()} context="Current bookings only" icon={Clock3} />
      <MetricCard label="Pending products" value={k.pendingProducts.toLocaleString()} context="Bookings requiring fulfilment" icon={PackageOpen} />
      <MetricCard label="Total profit" value={currency(k.totalProfit)} context="Latest normalized booking rows" icon={CircleDollarSign} />
    </section>

    <section className="card mt-6 p-5 sm:p-6"><div className="mb-4 flex items-center gap-2"><AlertTriangle size={18} className="text-amber-600" /><h2 className="font-semibold">Needs Attention</h2></div><div className="grid gap-2 lg:grid-cols-2">{(data.attention || []).map((item) => <Link to={item.href} key={item.label} className="group flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3 transition hover:border-accent-200 hover:bg-accent-50/40"><div><p className="text-sm font-semibold text-slate-800 group-hover:text-accent-700">{item.label}</p><p className="mt-1 text-xs text-slate-500">{item.context}</p></div><span className="text-slate-300 group-hover:text-accent-600">→</span></Link>)}</div></section>

    <div className="mt-6 grid gap-6 xl:grid-cols-[1.55fr_1fr]">
      <ChartCard title="Error trend" description="Errors linked to current bookings by issue date">
        <ResponsiveContainer width="100%" height="100%"><AreaChart data={data.errorTrend || []} margin={{ left: -20, right: 8, top: 8 }}><defs><linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#16846b" stopOpacity={0.2}/><stop offset="95%" stopColor="#16846b" stopOpacity={0}/></linearGradient></defs><CartesianGrid vertical={false} stroke="#eef1f0" /><XAxis dataKey="date" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} minTickGap={25}/><YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false}/><Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 12 }}/><Area type="monotone" dataKey="errors" stroke="#16846b" strokeWidth={2} fill="url(#areaFill)" /></AreaChart></ResponsiveContainer>
      </ChartCard>
      <ChartCard title="Error status" description="Resolution state for errors linked to current bookings">
        {(data.statusDistribution || []).length ? <ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={data.statusDistribution} dataKey="value" nameKey="status" innerRadius={70} outerRadius={98} paddingAngle={3}>{data.statusDistribution?.map((entry, index) => <Cell key={entry.status} fill={pieColors[index % pieColors.length]} />)}</Pie><Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 12 }}/></PieChart></ResponsiveContainer> : <ChartEmpty />}
      </ChartCard>
      <ChartCard title="Agent performance" description="Error rate; booking count is shown in parentheses">
        {agentData.length ? <ResponsiveContainer width="100%" height="100%"><BarChart data={agentData} layout="vertical" margin={{ left: 28, right: 18 }}><CartesianGrid horizontal={false} stroke="#eef1f0"/><XAxis type="number" unit="%" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false}/><YAxis type="category" dataKey="agentLabel" width={92} tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false}/><Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 12 }}/><Bar dataKey="errorRatePct" name="Error rate" fill="#16846b" radius={[0, 5, 5, 0]} maxBarSize={18}/></BarChart></ResponsiveContainer> : <ChartEmpty />}
      </ChartCard>
      <ChartCard title="Common error categories" description="Deterministic classification of current-booking issues">
        {(data.errorCategories || []).length ? <ResponsiveContainer width="100%" height="100%"><BarChart data={data.errorCategories} layout="vertical" margin={{ left: 45, right: 12 }}><CartesianGrid horizontal={false} stroke="#eef1f0"/><XAxis type="number" allowDecimals={false} tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false}/><YAxis type="category" dataKey="category" width={110} tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false}/><Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 12 }}/><Bar dataKey="value" name="Errors" fill="#64748b" radius={[0, 5, 5, 0]} maxBarSize={18}/></BarChart></ResponsiveContainer> : <ChartEmpty />}
      </ChartCard>
    </div>

    <section className="mt-6"><div className="mb-4"><h2 className="text-lg font-semibold">Key Insights</h2><p className="mt-1 text-xs text-slate-500">Calculated from SQL and workbook data — never invented by AI.</p></div><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{(data.insights || []).map((item) => <Link to={item.href} key={item.title} className="card p-5 transition hover:-translate-y-0.5 hover:border-accent-200"><p className="text-xs font-semibold uppercase tracking-wide text-accent-700">{item.title}</p><p className="mt-3 text-sm leading-6 text-slate-700">{item.text}</p></Link>)}</div></section>
    <p className="mt-6 text-right text-xs text-slate-400">{compact(k.totalErrors)} total error records retained, including unmatched history.</p>
  </>;
}

function ChartEmpty() { return <div className="grid h-full place-items-center text-sm text-slate-400">No matched data to chart</div>; }
