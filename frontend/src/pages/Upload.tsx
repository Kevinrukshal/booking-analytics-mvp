import { CheckCircle2, FileSpreadsheet, UploadCloud, XCircle } from "lucide-react";
import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { PageHeader } from "../components/ui/PageHeader";
import type { UploadSummary } from "../types";

export function UploadPage() {
  const input = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const [dragging, setDragging] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState<UploadSummary>();
  const [error, setError] = useState<string>();

  async function upload(file?: File) {
    if (!file || processing) return;
    if (!window.confirm("Replace the current dataset with this workbook? Only upload data you are authorized to process.")) return;
    if (!file.name.toLowerCase().endsWith(".xlsx")) {
      setError("Choose an .xlsx workbook.");
      return;
    }
    setProcessing(true);
    setError(undefined);
    setResult(undefined);
    const form = new FormData();
    form.append("file", file);
    try {
      setResult(await api<UploadSummary>("/api/uploads?replace=true", { method: "POST", body: form }));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Upload failed.");
    } finally {
      setProcessing(false);
    }
  }

  const summary = result?.summary as Record<string, number | unknown> | undefined;

  return <>
    <PageHeader title="Upload" description="Upload a monthly or full-year booking workbook." />
    <div className="mx-auto max-w-4xl">
        <button
          type="button"
          onClick={() => input.current?.click()}
          onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => { event.preventDefault(); setDragging(false); void upload(event.dataTransfer.files[0]); }}
          className={`card flex min-h-80 w-full flex-col items-center justify-center border-2 border-dashed p-10 text-center transition ${dragging ? "border-accent-500 bg-accent-50" : "hover:border-accent-300"}`}
        >
          <div className="rounded-2xl bg-accent-50 p-4 text-accent-700">
            {processing ? <FileSpreadsheet className="animate-pulse" size={30} /> : <UploadCloud size={30} />}
          </div>
          <h2 className="mt-5 text-xl font-semibold">{processing ? "Processing workbook…" : "Upload booking workbook"}</h2>
          <p className="mt-2 text-sm text-slate-500">{processing ? "Normalizing bookings, joining errors and calculating quality checks." : "Drop an .xlsx file here or choose a file"}</p>
          <span className="button mt-6">{processing ? "Please wait" : "Choose file"}</span>
          <p className="mt-3 text-xs text-slate-400">Maximum 100 MB · monthly and full-year files supported · macros are never executed</p>
        </button>
        <input ref={input} className="hidden" type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" onChange={(event) => void upload(event.target.files?.[0])} />

        {error && <div className="mt-5 flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700"><XCircle size={18} className="mt-0.5 shrink-0" /><div><p className="font-semibold">Import failed</p><p className="mt-1">{error}</p></div></div>}

        {result && <div className="card mt-5 p-6">
          <div className="flex items-start gap-3"><CheckCircle2 size={22} className="text-emerald-600" /><div><h2 className="font-semibold">Import completed</h2><p className="mt-1 text-sm text-slate-500">{result.filename}</p></div></div>
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            <Summary label="Bookings imported" value={result.bookingCount} />
            <Summary label="Error records" value={result.errorCount} />
            <Summary label="Unmatched errors" value={Number(summary?.unmatched_error_rows || 0)} />
            <Summary label="Duplicate refs merged" value={Number(summary?.duplicate_booking_references_merged || 0)} />
            <Summary label="Missing booking refs" value={Number(summary?.missing_booking_references || 0)} />
            <Summary label="Exact duplicate errors skipped" value={Number(summary?.duplicate_errors_skipped || 0)} />
          </div>
          <div className="mt-6 flex justify-end border-t border-slate-100 pt-5"><button className="button" onClick={() => navigate("/")}>View dashboard</button></div>
        </div>}
    </div>
  </>;
}

function Summary({ label, value }: { label: string; value: number }) {
  return <div className="rounded-xl bg-slate-50 px-4 py-3"><p className="text-xs text-slate-500">{label}</p><p className="mt-1 text-lg font-bold text-slate-900">{value.toLocaleString()}</p></div>;
}
