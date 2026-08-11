import type { ReactNode } from "react";

export function PageHeader({ title, description, actions }: { title: string; description: string; actions?: ReactNode }) {
  return <div className="mb-7 flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-[28px]">{title}</h1><p className="mt-1.5 text-sm text-slate-500">{description}</p></div>{actions}</div>;
}

