import { BarChart3, BookOpen, Bot, Menu, Upload, Users, X } from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

const navigation = [
  { label: "Overview", href: "/", icon: BarChart3 },
  { label: "Bookings", href: "/bookings", icon: BookOpen },
  { label: "Agents", href: "/agents", icon: Users },
  { label: "Errors", href: "/errors", icon: Bot },
  { label: "Upload", href: "/upload", icon: Upload },
];

function Sidebar({ close }: { close?: () => void }) {
  return <aside className="flex h-full w-60 flex-col border-r border-slate-200 bg-white px-4 py-5 lg:w-56"><div className="flex h-11 items-center gap-3 px-2"><div className="grid h-9 w-9 place-items-center rounded-xl bg-accent-600 text-sm font-bold text-white">BA</div><div><p className="text-sm font-bold text-slate-900">Booking Analytics</p><p className="text-[11px] text-slate-400">Operations clarity</p></div></div><nav className="mt-8 space-y-1">{navigation.map(({ label, href, icon: Icon }) => <NavLink key={href} to={href} end={href === "/"} onClick={close} className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${isActive ? "bg-accent-50 text-accent-700" : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"}`}><Icon size={18} strokeWidth={1.8} />{label}</NavLink>)}</nav><div className="mt-auto rounded-xl border border-slate-200 bg-slate-50 p-3"><p className="text-xs font-semibold text-slate-700">Data stays private</p><p className="mt-1 text-[11px] leading-4 text-slate-500">Excel files are processed by your private backend.</p></div></aside>;
}

export function AppLayout() {
  const [open, setOpen] = useState(false);
  return <div className="min-h-screen"><div className="fixed inset-y-0 left-0 z-30 hidden lg:block"><Sidebar /></div>{open && <div className="fixed inset-0 z-50 lg:hidden"><button className="absolute inset-0 bg-slate-950/25" aria-label="Close navigation" onClick={() => setOpen(false)} /><div className="relative h-full w-60"><Sidebar close={() => setOpen(false)} /><button className="absolute right-3 top-4 rounded-lg p-2 text-slate-500" onClick={() => setOpen(false)}><X size={20} /></button></div></div>}<header className="sticky top-0 z-20 flex h-16 items-center border-b border-slate-200 bg-white/90 px-4 backdrop-blur lg:hidden"><button className="rounded-xl border border-slate-200 p-2" onClick={() => setOpen(true)}><Menu size={19} /></button><span className="ml-3 text-sm font-bold">Booking Analytics</span></header><main className="px-4 py-7 sm:px-7 lg:ml-56 lg:px-9 lg:py-9"><div className="mx-auto max-w-[1500px]"><Outlet /></div></main></div>;
}
