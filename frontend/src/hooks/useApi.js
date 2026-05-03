import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * useApi
 * ------
 * Wraps fetch with:
 *  - base URL `/api`
 *  - Bearer auth header (read from localStorage `pst-auth-token` so we don't
 *    create a circular dep with AuthContext consumers)
 *  - JSON parsing + structured errors
 *  - {data, error, loading, refetch} return
 *
 * Pass an absolute URL (starting with `http`) to bypass the `/api` prefix.
 *
 * Options:
 *   - method, body, headers   : standard fetch
 *   - skip                    : when true, do not auto-fetch on mount
 *   - deps                    : extra deps that should re-trigger the fetch
 *   - emptyOn404 (default true) : treat 404 as empty data instead of error
 */
export default function useApi(path, options = {}) {
  const {
    method  = 'GET',
    body,
    headers = {},
    skip    = false,
    deps    = [],
    emptyOn404 = true,
  } = options;

  const [data,    setData]    = useState(null);
  const [error,   setError]   = useState(null);
  const [loading, setLoading] = useState(!skip);
  const abortRef = useRef(null);

  const buildUrl = useCallback((p) => {
    if (!p) return null;
    if (/^https?:\/\//i.test(p)) return p;
    return p.startsWith('/api') ? p : `/api${p.startsWith('/') ? '' : '/'}${p}`;
  }, []);

  const run = useCallback(async (overridePath, overrideOptions = {}) => {
    const url = buildUrl(overridePath ?? path);
    if (!url) return;

    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);

    let token = null;
    try { token = localStorage.getItem('pst-auth-token'); } catch { /* no-op */ }

    const finalHeaders = {
      'Accept': 'application/json',
      ...(body ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
      ...(overrideOptions.headers || {}),
    };

    const finalMethod = overrideOptions.method || method;
    const finalBody   = overrideOptions.body   ?? body;

    try {
      const res = await fetch(url, {
        method: finalMethod,
        headers: finalHeaders,
        credentials: 'include',
        body: finalBody && finalMethod !== 'GET' ? JSON.stringify(finalBody) : undefined,
        signal: controller.signal,
      });

      if (res.status === 404 && emptyOn404) {
        setData(null);
        setError(null);
        return null;
      }

      if (!res.ok) {
        let msg = `Request failed (${res.status})`;
        try {
          const errBody = await res.json();
          if (errBody?.message) msg = errBody.message;
          else if (errBody?.error) msg = errBody.error;
        } catch { /* not JSON */ }
        const e = new Error(msg);
        e.status = res.status;
        throw e;
      }

      // Some endpoints (e.g. DELETE) return no body
      const text = await res.text();
      const parsed = text ? JSON.parse(text) : null;
      setData(parsed);
      return parsed;
    } catch (err) {
      if (err.name === 'AbortError') return;
      setError(err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [path, method, body, headers, emptyOn404, buildUrl]);

  useEffect(() => {
    if (skip) { setLoading(false); return; }
    run();
    return () => { if (abortRef.current) abortRef.current.abort(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, skip, ...deps]);

  return { data, error, loading, refetch: run };
}

/**
 * apiFetch — imperative one-off call (POST/PUT/DELETE outside a hook).
 * Returns parsed JSON or throws.
 */
export async function apiFetch(path, { method = 'GET', body, headers = {} } = {}) {
  let token = null;
  try { token = localStorage.getItem('pst-auth-token'); } catch { /* no-op */ }
  const url = /^https?:\/\//i.test(path)
    ? path
    : (path.startsWith('/api') ? path : `/api${path.startsWith('/') ? '' : '/'}${path}`);

  const res = await fetch(url, {
    method,
    headers: {
      'Accept': 'application/json',
      ...(body ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    credentials: 'include',
    body: body && method !== 'GET' ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      const eb = await res.json();
      if (eb?.message) msg = eb.message;
      else if (eb?.error) msg = eb.error;
    } catch { /* */ }
    const e = new Error(msg);
    e.status = res.status;
    throw e;
  }
  const text = await res.text();
  return text ? JSON.parse(text) : null;
}
