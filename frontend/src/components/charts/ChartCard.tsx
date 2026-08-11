import type { ReactNode } from "react";

export function ChartCard({ title, description, children }: { title: string; description: string; children: ReactNode }) {
  return <section className="card min-w-0 p-5 sm:p-6"><div className="mb-5"><h2 className="font-semibold text-slate-900">{title}</h2><p className="mt-1 text-xs text-slate-500">{description}</p></div><div className="h-72">{children}</div></section>;
}

