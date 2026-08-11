import type { ReactNode } from "react";

const tones: Record<string, string> = {
  green: "bg-emerald-50 text-emerald-700 ring-emerald-600/15",
  amber: "bg-amber-50 text-amber-700 ring-amber-600/15",
  red: "bg-red-50 text-red-700 ring-red-600/15",
  gray: "bg-slate-100 text-slate-600 ring-slate-500/10",
};

export function Badge({ children, tone = "gray" }: { children: ReactNode; tone?: keyof typeof tones }) {
  return <span className={`inline-flex whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${tones[tone]}`}>{children}</span>;
}

export function statusTone(status?: string): keyof typeof tones {
  const value = (status || "").toLowerCase();
  if (["resolved", "sorted", "booked", "healthy", "matching", "checked"].some((key) => value.includes(key))) return "green";
  if (["pending", "watch", "allocated", "insufficient"].some((key) => value.includes(key))) return "amber";
  if (["open", "error", "attention", "critical", "high"].some((key) => value.includes(key))) return "red";
  return "gray";
}

