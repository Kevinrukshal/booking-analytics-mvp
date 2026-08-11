import { AlertCircle, Database, RefreshCw } from "lucide-react";
import { Link } from "react-router-dom";

export function LoadingState({ rows = 4 }: { rows?: number }) {
  return <div className="space-y-3">{Array.from({ length: rows }).map((_, index) => <div key={index} className="h-20 animate-pulse rounded-2xl bg-slate-200/60" />)}</div>;
}

export function ErrorState({ message, retry }: { message: string; retry?: () => void }) {
  return <div className="card flex min-h-64 flex-col items-center justify-center p-8 text-center"><AlertCircle className="mb-4 text-red-500" size={28} /><h3 className="font-semibold">Unable to load this page</h3><p className="mt-2 max-w-md text-sm text-slate-500">{message}</p>{retry && <button className="button-secondary mt-5" onClick={retry}><RefreshCw size={15} />Retry</button>}</div>;
}

export function EmptyDataset() {
  return <div className="card flex min-h-80 flex-col items-center justify-center p-10 text-center"><div className="mb-5 rounded-2xl bg-accent-50 p-4 text-accent-700"><Database size={28} /></div><h2 className="text-xl font-semibold">No workbook uploaded yet</h2><p className="mt-2 max-w-md text-sm leading-6 text-slate-500">Upload an Excel workbook to generate booking, agent and error analytics.</p><Link to="/upload" className="button mt-6">Upload workbook</Link></div>;
}

