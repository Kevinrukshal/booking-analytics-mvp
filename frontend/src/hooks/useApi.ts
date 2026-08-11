import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";

export function useApi<T>(path: string) {
  const [data, setData] = useState<T>();
  const [error, setError] = useState<string>();
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setLoading(true); setError(undefined);
    try { setData(await api<T>(path)); } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to load data."); } finally { setLoading(false); }
  }, [path]);
  useEffect(() => { void load(); }, [load]);
  return { data, error, loading, retry: load };
}

