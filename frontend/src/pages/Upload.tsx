import { Bot, CheckCircle2, FileSpreadsheet, LoaderCircle, UploadCloud, XCircle } from "lucide-react";
import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { PageHeader } from "../components/ui/PageHeader";
import { useApi } from "../hooks/useApi";
import type { UploadSummary } from "../types";

type AIResult = {
  category: string;
  subcategory: string;
  severity: string;
  summary: string;
  recommended_action: string;
};

export function UploadPage() {
  const input = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const [dragging, setDragging] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState<UploadSummary>();
  const [error, setError] = useState<string>();
  const aiStatus = useApi<{ enabled: boolean }>("/api/ai/status");
  const [issue, setIssue] = useState("pax name entered wrong in pnr");
  const [aiProcessing, setAiProcessing] = useState(false);
  const [aiResult, setAiResult] = useState<AIResult>();
  const [aiError, setAiError] = useState<string>();

  async function upload(file?: File) {
    if (!file) return;
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

  async function testAI() {
    setAiProcessing(true);
    setAiError(undefined);
    setAiResult(undefined);
    try {
      setAiResult(await api<AIResult>("/api/ai/classify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ issue }),
      }));
    } catch (cause) {
      setAiError(cause instanceof Error ? cause.message : "AI classification failed.");
    } finally {
      setAiProcessing(false);
    }
  }

  const summary = result?.summary as Record<string, number | unknown> | undefined;

  return <>
    <PageHeader title="Upload" description="Replace the current dataset and verify optional AI classification." />
    <div className="mx-auto grid max-w-6xl gap-6 xl:grid-cols-[1.25fr_.75fr]">
      <div>
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
          <p className="mt-3 text-xs text-slate-400">Maximum 25 MB · formulas are read as values · macros are never executed</p>
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
          <div className="mt-6 flex items-center justify-between border-t border-slate-100 pt-5"><p className="text-xs text-slate-500">AI classification {result.aiEnabled ? "enabled" : "disabled — deterministic categories are active"}.</p><button className="button" onClick={() => navigate("/")}>View dashboard</button></div>
        </div>}
      </div>

      <section className="card h-fit p-6">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3"><div className="rounded-xl bg-accent-50 p-2.5 text-accent-700"><Bot size={20} /></div><div><h2 className="font-semibold">Test AI classifier</h2><p className="mt-1 text-xs text-slate-500">Sends only this issue text to Gemini.</p></div></div>
          <span className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${aiStatus.data?.enabled ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>{aiStatus.data?.enabled ? "Enabled" : "Disabled"}</span>
        </div>
        <label className="mt-6 block text-xs font-semibold uppercase tracking-wide text-slate-500">Sample issue</label>
        <textarea className="mt-2 min-h-32 w-full resize-y rounded-xl border border-slate-200 p-3 text-sm leading-6 text-slate-700 focus:border-accent-500" value={issue} onChange={(event) => setIssue(event.target.value)} maxLength={4000} />
        <button className="button mt-3 w-full" disabled={!aiStatus.data?.enabled || aiProcessing || issue.trim().length < 3} onClick={() => void testAI()}>{aiProcessing ? <LoaderCircle className="animate-spin" size={16} /> : <Bot size={16} />}Classify issue</button>
        {!aiStatus.loading && !aiStatus.data?.enabled && <p className="mt-3 text-xs leading-5 text-slate-500">Add <code>GEMINI_API_KEY</code> and <code>GEMINI_MODEL</code> to the backend environment, then restart Docker.</p>}
        {aiError && <p className="mt-3 rounded-xl bg-red-50 p-3 text-xs text-red-700">{aiError}</p>}
        {aiResult && <div className="mt-4 space-y-3 rounded-xl bg-slate-50 p-4 text-sm"><div className="flex flex-wrap gap-2"><span className="rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-slate-700">{aiResult.category}</span><span className="rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-slate-700">{aiResult.severity}</span></div><p className="leading-6 text-slate-700">{aiResult.summary}</p><p className="text-xs leading-5 text-slate-500"><b>Recommended:</b> {aiResult.recommended_action}</p></div>}
      </section>
    </div>
  </>;
}

function Summary({ label, value }: { label: string; value: number }) {
  return <div className="rounded-xl bg-slate-50 px-4 py-3"><p className="text-xs text-slate-500">{label}</p><p className="mt-1 text-lg font-bold text-slate-900">{value.toLocaleString()}</p></div>;
}
