const API_URL = (import.meta.env.VITE_API_URL as string | undefined) || "";

export function queryString(params: Record<string, string | number | boolean | undefined | null>) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => { if (value !== undefined && value !== null && value !== "") query.set(key, String(value)); });
  return query.toString();
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Request failed" })) as { detail?: string };
    throw new Error(payload.detail || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export async function downloadFile(path: string, fallbackName: string) {
  const response = await fetch(`${API_URL}${path}`);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Export failed" })) as { detail?: string };
    throw new Error(payload.detail || `Export failed (${response.status})`);
  }
  const disposition = response.headers.get("Content-Disposition") || "";
  const matchedName = disposition.match(/filename="?([^";]+)"?/i)?.[1];
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = matchedName || fallbackName;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
