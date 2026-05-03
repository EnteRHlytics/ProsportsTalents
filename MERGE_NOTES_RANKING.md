# Merge Notes — Agent 3 (Rankings)

This document lists the exact wiring changes that need to be applied to
files agent 3 does not own.  Apply them at merge time.

## 1. `app/models/__init__.py`

Add the model export so `RankingPreset` is importable from
`app.models`:

```python
from .ranking_preset import RankingPreset

__all__.append('RankingPreset')
```

Place this near the other late `__all__.extend(...)` blocks at the bottom
of the file.

## 2. `app/api/__init__.py`

The new endpoints register themselves when the existing
`from app.api import ... rankings ...` line is executed, so **no change
is required** here — `rankings` is already in the import list.

If preset-related URLs need a dedicated namespace later, add:

```python
ranking_presets_ns = api.namespace('rankings/presets', description='User ranking presets')
```

But the current implementation registers via `@api.route(...)` only and
needs no namespace.

## 3. `frontend/src/App.jsx`

Add the two new routes inside the existing `<Routes>` block (alongside
the other top-level pages):

```jsx
import Rankings from './views/Rankings';
import RankingsCustomize from './views/RankingsCustomize';

// ...

<Route path="/rankings" element={<Rankings />} />
<Route path="/rankings/customize" element={<RankingsCustomize />} />
```

Optionally surface a navigation link in `Navbar` pointing to `/rankings`.

## 4. Database migration

Run:

```
flask db upgrade
```

The new revision `7c4a91d3e5a2` (depends on `f29d5d6ebc1b`) creates the
`ranking_presets` table.

## 5. Known limitations / verification gaps

* **`tests/test_rankings_api.py` cannot be executed in agent 3's worktree
  in isolation.**  The current `app/utils/__init__.py` imports from a
  missing `app/utils/cache` module, and `app/models/__init__.py` imports
  `app.models.prospect` / `app.models.api_key` which are owned by other
  agents.  Once those modules land, `pytest tests/test_rankings_api.py`
  should pass — the test file itself is complete and the API code was
  validated by spec-loading the service module directly (see
  `tests/test_ranking_service.py`, 16 tests, all passing).
* **`fan_perception` and `market_value` are placeholders.**  See the
  module docstring in `app/services/ranking_service.py`.  Replace once a
  survey / social-sentiment / contract data source is wired up.
* **Stat name conventions** assumed by the algorithm:
  `PointsPerGame`, `PassingYards`, `BattingAverage`, `Points`,
  `Goals`, `TrueShootingPct`, `PasserRating`, `OPS`, `PlusMinus`,
  `Assists`, `GamesPlayed` (also accepts `Games` / `GP`).  If the
  ingestion layer uses different names, update
  `SPORT_PERFORMANCE_STATS` / `SPORT_EFFICIENCY_STATS` /
  `GAMES_PLAYED_KEYS` accordingly.

## 6. Files added / changed by this agent

```
app/services/ranking_service.py      (new)
app/api/rankings.py                  (rewritten)
app/models/ranking_preset.py         (new)
migrations/versions/7c4a91d3e5a2_add_ranking_presets.py (new)
tests/test_ranking_service.py        (new)
tests/test_rankings_api.py           (extended)
frontend/src/views/Rankings.jsx                       (new)
frontend/src/views/RankingsCustomize.jsx              (new)
frontend/src/components/ranking/WeightSlider.jsx      (new)
frontend/src/components/ranking/RankingTable.jsx      (new)
frontend/src/components/ranking/ScoreBreakdown.jsx    (new)
docs/phase3_notes.md                                  (updated)
MERGE_NOTES_RANKING.md                                (this file)
```
