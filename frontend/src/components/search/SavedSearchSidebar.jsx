import { Bookmark, Trash2, Plus } from 'lucide-react';

/**
 * Sidebar listing the current user's saved searches.
 *
 * Each entry can be loaded back into the active filters via
 * ``onLoad`` or removed via ``onDelete``. ``onSaveCurrent`` opens
 * the save modal in the parent view.
 */
export default function SavedSearchSidebar({
  searches,
  loading,
  error,
  onLoad,
  onDelete,
  onSaveCurrent,
  activeId,
}) {
  return (
    <aside
      className="bg-surface-800 border border-surface-700 rounded-xl p-5 text-slate-100"
      style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}
      aria-label="Saved searches"
    >
      <div className="flex items-center justify-between mb-4">
        <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-300">
          <Bookmark size={14} /> Saved
        </h2>
        <button
          type="button"
          onClick={onSaveCurrent}
          className="flex items-center gap-1 text-xs text-orange-400 hover:text-orange-300"
          title="Save current filters as a new search"
        >
          <Plus size={12} /> New
        </button>
      </div>

      {loading && (
        <p className="text-xs text-slate-500">Loading saved searches...</p>
      )}
      {error && (
        <p className="text-xs text-red-300 break-words">{error}</p>
      )}
      {!loading && !error && searches.length === 0 && (
        <p className="text-xs text-slate-500">
          No saved searches yet. Set up some filters and click "Save search".
        </p>
      )}

      <ul className="space-y-1">
        {searches.map((s) => {
          const isActive = activeId === s.id;
          return (
            <li
              key={s.id}
              className={`group flex items-center justify-between gap-2 rounded-md px-2 py-1.5 cursor-pointer transition-colors ${
                isActive
                  ? 'bg-orange-500/10 border border-orange-500/40 text-orange-200'
                  : 'hover:bg-surface-700 border border-transparent text-slate-300'
              }`}
            >
              <button
                type="button"
                onClick={() => onLoad(s)}
                className="flex-1 text-left text-sm truncate"
                title={s.name}
              >
                {s.name}
              </button>
              <button
                type="button"
                onClick={() => onDelete(s)}
                className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-400 transition-opacity"
                title={`Delete "${s.name}"`}
                aria-label={`Delete saved search ${s.name}`}
              >
                <Trash2 size={14} />
              </button>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
