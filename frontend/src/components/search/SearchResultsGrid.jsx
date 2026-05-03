import { Link } from 'react-router-dom';
import { ChevronLeft, ChevronRight, User as UserIcon } from 'lucide-react';

/**
 * Grid of athlete result cards with paging controls.
 *
 * Pure presentational; the parent owns the search state and provides
 * the current page metadata so we can render Prev/Next buttons.
 */
export default function SearchResultsGrid({
  results,
  loading,
  error,
  total,
  page,
  pages,
  hasNext,
  hasPrev,
  onPageChange,
}) {
  if (loading) {
    return (
      <div className="text-center py-16 text-slate-400 text-sm" role="status">
        Searching...
      </div>
    );
  }

  if (error) {
    return (
      <div className="border border-red-700/40 bg-red-950/30 text-red-200 rounded-md p-4 text-sm">
        {error}
      </div>
    );
  }

  if (!results || results.length === 0) {
    return (
      <div className="text-center py-16">
        <UserIcon size={36} className="mx-auto mb-2 text-slate-600" />
        <p className="text-slate-400 text-sm">No athletes match your filters.</p>
        <p className="text-slate-500 text-xs mt-1">Try clearing some filters or broadening the age range.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-3 text-xs text-slate-400">
        <span>
          Showing {results.length} of {total} athlete{total === 1 ? '' : 's'}
        </span>
        <span>
          Page {page} of {pages || 1}
        </span>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {results.map((a) => (
          <AthleteCard key={a.athlete_id} athlete={a} />
        ))}
      </div>

      <div className="flex items-center justify-center gap-2 mt-6">
        <button
          type="button"
          onClick={() => onPageChange(Math.max(1, page - 1))}
          disabled={!hasPrev}
          className="flex items-center gap-1 px-3 py-1.5 rounded-md border border-surface-700 text-sm text-slate-300 disabled:opacity-40 hover:border-orange-500 hover:text-orange-400 transition-colors"
        >
          <ChevronLeft size={14} /> Prev
        </button>
        <span className="px-3 py-1.5 text-sm text-slate-400">
          {page} / {pages || 1}
        </span>
        <button
          type="button"
          onClick={() => onPageChange(page + 1)}
          disabled={!hasNext}
          className="flex items-center gap-1 px-3 py-1.5 rounded-md border border-surface-700 text-sm text-slate-300 disabled:opacity-40 hover:border-orange-500 hover:text-orange-400 transition-colors"
        >
          Next <ChevronRight size={14} />
        </button>
      </div>
    </div>
  );
}

function AthleteCard({ athlete }) {
  const name = athlete.user?.full_name || `Athlete ${athlete.athlete_id}`;
  const initials = name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((n) => n[0])
    .join('')
    .toUpperCase();

  return (
    <Link
      to={`/athletes/${athlete.athlete_id}`}
      className="block bg-surface-800 hover:bg-surface-700 transition-colors rounded-lg overflow-hidden border border-surface-700"
      style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}
    >
      <div className="aspect-square bg-gradient-to-br from-surface-700 to-surface-900 flex items-center justify-center">
        {athlete.profile_image_url ? (
          // eslint-disable-next-line jsx-a11y/img-redundant-alt
          <img
            src={athlete.profile_image_url}
            alt={`Photo of ${name}`}
            className="w-full h-full object-cover"
          />
        ) : (
          <span className="text-3xl font-bold text-slate-400">{initials}</span>
        )}
      </div>
      <div className="p-3">
        <div className="font-semibold text-sm text-slate-100 truncate">{name}</div>
        <div className="text-xs text-slate-400 mt-0.5">
          {athlete.current_team || 'Free Agent'}
        </div>
        <div className="flex items-center justify-between mt-1.5 text-[11px] text-slate-500">
          <span>{athlete.primary_sport?.code || 'Unknown sport'}</span>
          {athlete.overall_rating != null && (
            <span className="text-orange-400 font-semibold">{athlete.overall_rating}</span>
          )}
        </div>
      </div>
    </Link>
  );
}
