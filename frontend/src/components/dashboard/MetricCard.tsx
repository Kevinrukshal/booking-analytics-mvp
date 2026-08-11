import type { LucideIcon } from "lucide-react";

export function MetricCard({ label, value, context, icon: Icon }: { label: string; value: string; context: string; icon: LucideIcon }) {
  return <div className="card p-5"><div className="flex items-center justify-between"><p className="text-sm font-medium text-slate-500">{label}</p><Icon size={17} className="text-slate-400" /></div><p className="mt-4 text-3xl font-bold tracking-tight text-slate-900">{value}</p><p className="mt-2 truncate text-xs text-slate-500">{context}</p></div>;
}

