import { useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, Save, Users, Trophy, Filter as FilterIcon } from 'lucide-react';

import FilterPanel from '../components/search/FilterPanel';
import SearchResultsGrid from '../components/search/SearchResultsGrid';
import SavedSearchSidebar from '../components/search/SavedSearchSidebar';
import SaveSearchModal from '../components/search/SaveSearchModal';
import ExportButtons from '../components/common/ExportButtons';

// ---------------------------------------------------------------------------
// Local API helper.
//
// NOTE: The shared ``useApi`` hook from ``frontend/src/hooks/useApi.js`` was
// not available at the time this view was written (Agent 1 owns that file).
// Until it exists, we use a local fetch wrapper. When ``useApi`` lands,
// these helpers can be replaced 1:1.
// ---------------------------------------------------------------------------
async function apiRequest(path, opts = {}) {
  const res = await fetch(path, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(opts.headers || {}),
    },
    ...opts,
  });
  const text = await res.text();
  let body = null;
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = text;
    }
  }
  if (!res.ok) {
    const msg = (body && (body.message || body.error)) || `Request failed (${res.status})`;
    const err = new Error(msg);
    err.status = res.status;
    err.body = body;
    throw err;
  }
  return body;
}

// ---------------------------------------------------------------------------
// URL <-> filter state synchronisation.
// ---------------------------------------------------------------------------
const FILTER_KEYS = [
  'q', 'sport', 'position', 'team',
  'min_age', 'max_age',
  'min_height', 'max_height',
  'min_weight', 'max_weight',
  'available', // 'true' or ''
];

const TAB_KEY = 'tab'; // all | nba | nfl | mlb | nhl | available | top
const PAGE_KEY = 'page';

const TABS = [
  { key: 'all',       label: 'All',       icon: Users  },
  { key: 'nba',       label: 'NBA',       icon: Trophy },
  { key: 'nfl',       label: 'NFL',       icon: Trophy },
  { key: 'mlb',       label: 'MLB',       icon: Trophy },
  { key: 'nhl',       label: 'NHL',       icon: Trophy },
  { key: 'available', label: 'Available', icon: Users  },
  { key: 'top',       label: 'Top',       icon: Trophy },
];

const EMPTY_FILTERS = FILTER_KEYS.reduce((acc, k) => ({ ...acc, [k]: '' }), {});

function readFiltersFromParams(params) {
  const out = { ...EMPTY_FILTERS };
  for (const k of FILTER_KEYS) {
    const v = params.get(k);
    if (v != null) out[k] = v;
  }
  return out;
}

/**
 * Build the querystring sent to ``/api/athletes/search`` from the
 * current filters + tab + page state.
 */
function buildSearchQuery(filters, tab, page) {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(filters)) {
    if (v == null || v === '') continue;
    if (k === 'available') {
      // The available toggle maps to the backend's ``filter=available`` tab.
      // It is layered with the tab below — see logic.
      continue;
    }
    sp.set(k, v);
  }
  // Tab maps to the backend ``filter`` param.
  if (tab && tab !== 'all') {
    sp.set('filter', tab);
  } else if (filters.available === 'true') {
    sp.set('filter', 'available');
  }
  sp.set('page', String(page || 1));
  sp.set('per_page', '24');
  return sp.toString();
}

export default function Discover() {
  const [params, setParams] = useSearchParams();

  const [filters, setFilters] = useState(() => readFiltersFromParams(params));
  const [tab, setTab] = useState(() => params.get(TAB_KEY) || 'all');
  const [page, setPage] = useState(() => Number(params.get(PAGE_KEY)) || 1);

  const [results, setResults] = useState([]);
  const [meta, setMeta] = useState({ total: 0, pages: 1, hasNext: false, hasPrev: false });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [savedSearches, setSavedSearches] = useState([]);
  const [activeSavedId, setActiveSavedId] = useState(null);
  const [savedLoading, setSavedLoading] = useState(false);
  const [savedError, setSavedError] = useState(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [modalBusy, setModalBusy] = useState(false);
  const [modalError, setModalError] = useState(null);

  // ---- URL sync ---------------------------------------------------------
  useEffect(() => {
    const next = new URLSearchParams();
    for (const [k, v] of Object.entries(filters)) {
      if (v != null && v !== '') next.set(k, v);
    }
    if (tab && tab !== 'all') next.set(TAB_KEY, tab);
    if (page && page > 1) next.set(PAGE_KEY, String(page));
    setParams(next, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, tab, page]);

  // ---- Search request ---------------------------------------------------
  const fetchResults = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const qs = buildSearchQuery(filters, tab, page);
      const data = await apiRequest(`/api/athletes/search?${qs}`);
      setResults(data.results || []);
      setMeta({
        total: data.total ?? (data.results || []).length,
        pages: data.pages ?? 1,
        hasNext: !!data.has_next,
        hasPrev: !!data.has_prev,
      });
    } catch (e) {
      setError(e.message || 'Failed to load athletes');
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [filters, tab, page]);

  useEffect(() => { fetchResults(); }, [fetchResults]);

  // ---- Saved searches ---------------------------------------------------
  const loadSavedSearches = useCallback(async () => {
    setSavedLoading(true);
    setSavedError(null);
    try {
      const data = await apiRequest('/api/saved-searches');
      setSavedSearches(Array.isArray(data) ? data : []);
    } catch (e) {
      if (e.status === 401) {
        // Not signed in — silently hide saved searches; user can still search.
        setSavedSearches([]);
        setSavedError('Sign in to save and re-use searches.');
      } else {
        setSavedError(e.message || 'Failed to load saved searches');
      }
    } finally {
      setSavedLoading(false);
    }
  }, []);

  useEffect(() => { loadSavedSearches(); }, [loadSavedSearches]);

  const handleLoadSaved = (search) => {
    const saved = search.params || {};
    const next = { ...EMPTY_FILTERS };
    for (const k of FILTER_KEYS) {
      if (saved[k] != null) next[k] = String(saved[k]);
    }
    setFilters(next);
    setTab(saved.tab || saved.filter || 'all');
    setPage(1);
    setActiveSavedId(search.id);
  };

  const handleDeleteSaved = async (search) => {
    if (!window.confirm(`Delete saved search "${search.name}"?`)) return;
    try {
      await apiRequest(`/api/saved-searches/${search.id}`, { method: 'DELETE' });
      if (activeSavedId === search.id) setActiveSavedId(null);
      loadSavedSearches();
    } catch (e) {
      alert(e.message || 'Failed to delete saved search');
    }
  };

  const handleSaveCurrent = async (name) => {
    setModalBusy(true);
    setModalError(null);
    try {
      const payload = {
        name,
        params: {
          ...Object.fromEntries(
            Object.entries(filters).filter(([, v]) => v != null && v !== '')
          ),
          tab,
        },
      };
      const created = await apiRequest('/api/saved-searches', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      setActiveSavedId(created.id);
      setModalOpen(false);
      loadSavedSearches();
    } catch (e) {
      setModalError(e.message || 'Failed to save search');
    } finally {
      setModalBusy(false);
    }
  };

  const onResetFilters = () => {
    setFilters({ ...EMPTY_FILTERS });
    setTab('all');
    setPage(1);
    setActiveSavedId(null);
  };

  const defaultName = useMemo(() => {
    const bits = [];
    if (filters.sport) bits.push(filters.sport);
    if (filters.position) bits.push(filters.position);
    if (filters.team) bits.push(filters.team);
    if (filters.q) bits.push(`"${filters.q}"`);
    if (tab && tab !== 'all') bits.push(`#${tab}`);
    return bits.join(' ').slice(0, 80) || 'My search';
  }, [filters, tab]);

  // Filter params suitable for the export endpoint — drop empty values and add tab.
  const exportParams = useMemo(() => {
    const out = {};
    for (const [k, v] of Object.entries(filters)) {
      if (v != null && v !== '') out[k] = v;
    }
    if (tab && tab !== 'all') out.filter = tab;
    return out;
  }, [filters, tab]);

  return (
    <div className="px-4 sm:px-8 py-6 max-w-[1400px] mx-auto">
      <header className="mb-6 flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-3xl font-bold text-slate-100">Discover Athletes</h1>
          <p className="text-sm text-slate-400 mt-1">
            Search, filter, and save lists of athletes across NBA, NFL, MLB, NHL, and Soccer.
          </p>
        </div>
        <ExportButtons type="search" params={exportParams} />
      </header>

      {/* League / quick filter tabs */}
      <nav className="flex flex-wrap gap-2 mb-5" role="tablist" aria-label="League filter">
        {TABS.map((t) => {
          const Icon = t.icon;
          const active = tab === t.key;
          return (
            <button
              key={t.key}
              role="tab"
              aria-selected={active}
              onClick={() => { setTab(t.key); setPage(1); }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm border transition-colors ${
                active
                  ? 'bg-orange-500 border-orange-500 text-white'
                  : 'bg-surface-800 border-surface-700 text-slate-300 hover:border-orange-400'
              }`}
            >
              <Icon size={14} /> {t.label}
            </button>
          );
        })}
      </nav>

      {/* Free-text search bar + save button */}
      <div className="flex flex-col sm:flex-row gap-2 mb-5">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="search"
            value={filters.q || ''}
            onChange={(e) => { setFilters({ ...filters, q: e.target.value }); setPage(1); }}
            placeholder="Search by name, position, or team..."
            className="w-full pl-9 pr-3 py-2 rounded-md bg-surface-800 border border-surface-700 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-orange-500"
          />
        </div>
        <button
          type="button"
          onClick={() => { setModalError(null); setModalOpen(true); }}
          className="flex items-center justify-center gap-2 px-4 py-2 rounded-md bg-orange-500 hover:bg-orange-400 text-white text-sm font-semibold"
        >
          <Save size={14} /> Save search
        </button>
      </div>

      {/* Three-column layout: filters | results | saved */}
      <div className="grid gap-5 lg:grid-cols-[260px_minmax(0,1fr)_240px]">
        <FilterPanel
          filters={filters}
          onChange={(next) => { setFilters(next); setPage(1); }}
          onReset={onResetFilters}
        />

        <main aria-live="polite">
          <SearchResultsGrid
            results={results}
            loading={loading}
            error={error}
            total={meta.total}
            page={page}
            pages={meta.pages}
            hasNext={meta.hasNext}
            hasPrev={meta.hasPrev}
            onPageChange={setPage}
          />
        </main>

        <SavedSearchSidebar
          searches={savedSearches}
          loading={savedLoading}
          error={savedError}
          onLoad={handleLoadSaved}
          onDelete={handleDeleteSaved}
          onSaveCurrent={() => { setModalError(null); setModalOpen(true); }}
          activeId={activeSavedId}
        />
      </div>

      <SaveSearchModal
        open={modalOpen}
        defaultName={defaultName}
        onSubmit={handleSaveCurrent}
        onClose={() => setModalOpen(false)}
        busy={modalBusy}
        error={modalError}
      />

      {/* Tiny accessibility hint for the icon-only filter sidebar header. */}
      <span className="sr-only" aria-hidden="true"><FilterIcon /></span>
    </div>
  );
}
