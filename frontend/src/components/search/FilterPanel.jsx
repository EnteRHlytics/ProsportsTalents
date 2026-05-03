import { Filter, X, RotateCcw } from 'lucide-react';

/**
 * Sport-aware filter panel for the Discover view.
 *
 * The set of valid positions narrows based on the selected sport.
 * All filter values live in the parent's state so the URL can stay
 * in sync via ``useSearchParams``.
 */

const SPORT_OPTIONS = [
  { code: 'NBA', label: 'NBA' },
  { code: 'NFL', label: 'NFL' },
  { code: 'MLB', label: 'MLB' },
  { code: 'NHL', label: 'NHL' },
  { code: 'SOC', label: 'Soccer' },
];

const POSITIONS_BY_SPORT = {
  NBA: ['PG', 'SG', 'SF', 'PF', 'C'],
  NFL: ['QB', 'RB', 'WR', 'TE', 'OL', 'DL', 'LB', 'CB', 'S', 'K', 'P'],
  MLB: ['P', 'C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'DH'],
  NHL: ['C', 'LW', 'RW', 'D', 'G'],
  SOC: ['GK', 'DF', 'MF', 'FW'],
};

export default function FilterPanel({ filters, onChange, onReset }) {
  const positions = filters.sport ? POSITIONS_BY_SPORT[filters.sport] || [] : [];

  const update = (patch) => onChange({ ...filters, ...patch });

  return (
    <aside
      className="bg-surface-800 border border-surface-700 rounded-xl p-5 text-slate-100"
      style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}
      aria-label="Search filters"
    >
      <div className="flex items-center justify-between mb-4">
        <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-300">
          <Filter size={14} /> Filters
        </h2>
        <button
          type="button"
          onClick={onReset}
          className="flex items-center gap-1 text-xs text-slate-400 hover:text-orange-400 transition-colors"
          title="Reset all filters"
        >
          <RotateCcw size={12} /> Reset
        </button>
      </div>

      <div className="space-y-4">
        {/* Sport */}
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">Sport</label>
          <select
            value={filters.sport || ''}
            onChange={(e) => update({ sport: e.target.value || '', position: '' })}
            className="w-full px-3 py-2 rounded-md bg-surface-900 border border-surface-700 text-sm text-slate-100 focus:outline-none focus:border-orange-500"
          >
            <option value="">All sports</option>
            {SPORT_OPTIONS.map((s) => (
              <option key={s.code} value={s.code}>{s.label}</option>
            ))}
          </select>
        </div>

        {/* Position */}
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">Position</label>
          <select
            value={filters.position || ''}
            onChange={(e) => update({ position: e.target.value })}
            disabled={!filters.sport}
            className="w-full px-3 py-2 rounded-md bg-surface-900 border border-surface-700 text-sm text-slate-100 disabled:opacity-50 focus:outline-none focus:border-orange-500"
          >
            <option value="">All positions</option>
            {positions.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
          {!filters.sport && (
            <p className="text-[10px] text-slate-500 mt-1">Select a sport to filter by position.</p>
          )}
        </div>

        {/* Team */}
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">Team</label>
          <input
            type="text"
            value={filters.team || ''}
            onChange={(e) => update({ team: e.target.value })}
            placeholder="e.g. Lakers"
            className="w-full px-3 py-2 rounded-md bg-surface-900 border border-surface-700 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-orange-500"
          />
        </div>

        {/* Age range */}
        <RangeRow
          label="Age"
          unit="yrs"
          minValue={filters.min_age}
          maxValue={filters.max_age}
          onMin={(v) => update({ min_age: v })}
          onMax={(v) => update({ max_age: v })}
          rangeMin={16}
          rangeMax={50}
        />

        {/* Height range */}
        <RangeRow
          label="Height"
          unit="cm"
          minValue={filters.min_height}
          maxValue={filters.max_height}
          onMin={(v) => update({ min_height: v })}
          onMax={(v) => update({ max_height: v })}
          rangeMin={150}
          rangeMax={230}
        />

        {/* Weight range */}
        <RangeRow
          label="Weight"
          unit="kg"
          minValue={filters.min_weight}
          maxValue={filters.max_weight}
          onMin={(v) => update({ min_weight: v })}
          onMax={(v) => update({ max_weight: v })}
          rangeMin={50}
          rangeMax={150}
        />

        {/* Contract status toggle */}
        <div className="flex items-center justify-between pt-2 border-t border-surface-700">
          <label htmlFor="freeagent-toggle" className="text-sm text-slate-300">
            Free agents only
          </label>
          <button
            id="freeagent-toggle"
            type="button"
            role="switch"
            aria-checked={filters.available === 'true'}
            onClick={() => update({ available: filters.available === 'true' ? '' : 'true' })}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              filters.available === 'true' ? 'bg-orange-500' : 'bg-surface-700'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                filters.available === 'true' ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      </div>
    </aside>
  );
}

function RangeRow({ label, unit, minValue, maxValue, onMin, onMax, rangeMin, rangeMax }) {
  return (
    <div>
      <div className="flex justify-between text-xs font-medium text-slate-400 mb-1">
        <span>{label} ({unit})</span>
        {(minValue || maxValue) && (
          <button
            type="button"
            onClick={() => { onMin(''); onMax(''); }}
            className="text-slate-500 hover:text-orange-400"
            title={`Clear ${label.toLowerCase()} range`}
          >
            <X size={12} />
          </button>
        )}
      </div>
      <div className="flex items-center gap-2">
        <input
          type="number"
          inputMode="numeric"
          min={rangeMin}
          max={rangeMax}
          value={minValue || ''}
          onChange={(e) => onMin(e.target.value)}
          placeholder={`min ${rangeMin}`}
          className="w-full px-2 py-1.5 rounded-md bg-surface-900 border border-surface-700 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-orange-500"
        />
        <span className="text-slate-500 text-sm">–</span>
        <input
          type="number"
          inputMode="numeric"
          min={rangeMin}
          max={rangeMax}
          value={maxValue || ''}
          onChange={(e) => onMax(e.target.value)}
          placeholder={`max ${rangeMax}`}
          className="w-full px-2 py-1.5 rounded-md bg-surface-900 border border-surface-700 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-orange-500"
        />
      </div>
    </div>
  );
}
