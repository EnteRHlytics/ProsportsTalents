import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

/**
 * AuthContext
 * ------------
 * Lightweight auth context for the ProsportsTalents frontend.
 *
 * Backend assumption (Agent 1):
 *   - GET  /api/auth/me   -> { user: {...}, roles: ["agent","admin",...] } | 401
 *   - POST /api/auth/logout
 *   - SSO login is initiated via redirect to /api/auth/login/<provider>
 *
 * If the backend isn't ready yet (404/401/network), we fall back to an
 * unauthenticated state so the rest of the app can still render.
 */

const STORAGE_TOKEN_KEY = 'pst-auth-token';
const STORAGE_USER_KEY  = 'pst-auth-user';

const AuthContext = createContext({
  user: null,
  roles: [],
  token: null,
  loading: false,
  hasRole: () => false,
  login: () => {},
  logout: () => {},
  refresh: () => {},
});

function readStorage(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}
function writeStorage(key, value) {
  try {
    if (value === null || value === undefined) localStorage.removeItem(key);
    else localStorage.setItem(key, value);
  } catch { /* ignore */ }
}

export function AuthProvider({ children }) {
  const [user, setUser]   = useState(() => {
    const raw = readStorage(STORAGE_USER_KEY);
    if (!raw) return null;
    try { return JSON.parse(raw); } catch { return null; }
  });
  const [roles, setRoles] = useState(() => {
    const raw = readStorage(STORAGE_USER_KEY);
    if (!raw) return [];
    try { return JSON.parse(raw)?.roles || []; } catch { return []; }
  });
  const [token, setToken] = useState(() => readStorage(STORAGE_TOKEN_KEY));
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const headers = {};
      const t = readStorage(STORAGE_TOKEN_KEY);
      if (t) headers.Authorization = `Bearer ${t}`;
      const res = await fetch('/api/auth/me', { headers, credentials: 'include' });
      if (!res.ok) {
        // 401 / 404 = treat as logged out, no console noise on first run
        setUser(null); setRoles([]);
        writeStorage(STORAGE_USER_KEY, null);
        return;
      }
      const data = await res.json();
      const u = data.user || data;
      const r = data.roles || u?.roles || [];
      setUser(u); setRoles(r);
      writeStorage(STORAGE_USER_KEY, JSON.stringify({ ...u, roles: r }));
    } catch {
      setUser(null); setRoles([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const login = useCallback((provider = 'google') => {
    // SSO is a redirect-based flow per the requirements doc.
    // Caller can pass a provider; default to google.
    const target = `/api/auth/login/${provider}`;
    if (typeof window !== 'undefined') window.location.href = target;
  }, []);

  const logout = useCallback(async () => {
    try { await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' }); }
    catch { /* ignore */ }
    setUser(null); setRoles([]); setToken(null);
    writeStorage(STORAGE_USER_KEY, null);
    writeStorage(STORAGE_TOKEN_KEY, null);
  }, []);

  const hasRole = useCallback((role) => {
    if (!role) return false;
    if (Array.isArray(role)) return role.some(r => roles.includes(r));
    return roles.includes(role);
  }, [roles]);

  const value = useMemo(() => ({
    user, roles, token, loading,
    hasRole, login, logout, refresh,
  }), [user, roles, token, loading, hasRole, login, logout, refresh]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}

export default AuthContext;
