import { useEffect, useState } from 'react';
import { X } from 'lucide-react';

/**
 * Modal that prompts the user for a name and saves the current
 * filter set. Submitting calls ``onSubmit(name)``; the parent owns
 * the network request.
 */
export default function SaveSearchModal({
  open,
  defaultName,
  onSubmit,
  onClose,
  busy,
  error,
}) {
  const [name, setName] = useState(defaultName || '');

  useEffect(() => {
    if (open) setName(defaultName || '');
  }, [open, defaultName]);

  if (!open) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4"
      role="dialog"
      aria-modal="true"
      aria-label="Save search"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="bg-surface-800 border border-surface-700 rounded-xl shadow-xl w-full max-w-md p-6 text-slate-100"
        style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}
      >
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold">Save this search</h2>
            <p className="text-xs text-slate-400 mt-1">
              Give your search a memorable name. You can re-load it later from the sidebar.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-100"
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <label htmlFor="save-search-name" className="block text-xs font-medium text-slate-400 mb-1">
            Name
          </label>
          <input
            id="save-search-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Available NBA point guards"
            autoFocus
            maxLength={120}
            className="w-full px-3 py-2 rounded-md bg-surface-900 border border-surface-700 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-orange-500"
          />

          {error && (
            <p className="text-xs text-red-300 mt-2">{error}</p>
          )}

          <div className="flex justify-end gap-2 mt-5">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 text-sm text-slate-300 hover:text-slate-100"
              disabled={busy}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={busy || !name.trim()}
              className="px-3 py-1.5 rounded-md bg-orange-500 text-white text-sm font-semibold hover:bg-orange-400 disabled:opacity-50"
            >
              {busy ? 'Saving...' : 'Save search'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
