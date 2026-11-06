import { useState, type FormEvent, type ReactNode } from "react";
import { api, setAccessToken } from "../../api/client";

export function AccessGate({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function unlock(event: FormEvent) {
    event.preventDefault();
    setBusy(true); setError(""); setAccessToken(token);
    try {
      await api("/api/session");
      setToken(""); setReady(true);
    } catch {
      setAccessToken(""); setToken("");
      setError("Unable to unlock. Check your access token and server configuration.");
    } finally { setBusy(false); }
  }
  if (ready) return <><div className="fixed bottom-4 right-4 z-50"><button className="button" onClick={() => { setAccessToken(""); setReady(false); }}>Lock dashboard</button></div>{children}</>;
  return <main className="mx-auto max-w-md px-6 py-20"><form className="card space-y-5 p-8" onSubmit={unlock}>
    <h1 className="text-2xl font-bold">Booking Analytics</h1>
    <p className="text-sm text-slate-600">Enter your access token to open this dashboard. It is forgotten when you lock or reload this page.</p>
    <label className="block">Access token<input className="mt-2 block w-full rounded border p-2" type="password" autoComplete="off" required value={token} onChange={event => setToken(event.target.value)} /></label>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    <button className="button" disabled={busy}>{busy ? "Checking..." : "Unlock dashboard"}</button>
  </form></main>;
}
