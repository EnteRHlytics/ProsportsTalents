# Merge Notes — Agent 4 (Exports)

This worktree adds **PDF + Excel export** for athletes, search results, and
rankings. Because Agent 4's `boundaries` forbid touching
`app/api/__init__.py`, `app/models/__init__.py`, and other agents' views, a
few small wiring edits are required at merge time.

## 1. Register the exports namespace in `app/api/__init__.py`

Add the namespace to the existing import line and call `add_namespace`
(Flask-RESTX) so the routes are discovered:

```python
# app/api/__init__.py

# (existing) -------------------------------------------------------------
from app.api import routes, athletes, skills, rankings, keys, prospects  # noqa: E402

# (add) -----------------------------------------------------------------
from app.api.exports import ns as exports_ns  # noqa: E402
api.add_namespace(exports_ns, path='/api/exports')
```

That registers the following routes:

| Method | Path                                                          |
| ------ | ------------------------------------------------------------- |
| GET    | `/api/exports/athletes/<athlete_id>.pdf`                      |
| GET    | `/api/exports/athletes/<athlete_id>.xlsx`                     |
| GET    | `/api/exports/search.pdf?<same params as /api/athletes/search>` |
| GET    | `/api/exports/search.xlsx?<...>`                              |
| GET    | `/api/exports/rankings.pdf?sport=...&preset_id=...`           |
| GET    | `/api/exports/rankings.xlsx?sport=...&preset_id=...`          |

All routes are `@login_or_token_required`.

## 2. `app/models/__init__.py`

**No change required.** The export services import models lazily inside the
service functions to avoid pulling in optional models at module import time.
If the `app.models` package import order ever shifts, the export services
will continue to work as long as `AthleteProfile`, `AthleteStat`,
`AthleteSkill`, `User`, `Sport`, and `Position` remain in `app.models`.

## 3. Front-end button wiring

`frontend/src/components/common/ExportButtons.jsx` exposes three modes:

```jsx
<ExportButtons type="athlete"  id={athleteId} />          // single athlete
<ExportButtons type="search"   params={searchQuery} />    // search list
<ExportButtons type="rankings" params={{ sport, preset_id }} />
```

Drop-in spots after merge (Agent 2 / Agent 3 own these views):

- **Discover / Search view** (Agent 2):
  - File: `frontend/src/views/Discover.jsx` (or wherever Agent 2 lands the
    search results page).
  - Place beside the page title, e.g. inside the header row above the
    results grid.
  - Pass the same query state currently used to fetch
    `/api/athletes/search` as the `params` prop:
    ```jsx
    <ExportButtons type="search" params={{ q, sport, position, team, min_age, max_age }} />
    ```

- **Rankings view** (Agent 3):
  - File: `frontend/src/views/Rankings.jsx` (or whatever Agent 3 names it).
  - Place beside the title or near the sport / preset selector.
    ```jsx
    <ExportButtons type="rankings" params={{ sport: selectedSport, preset_id: selectedPresetId }} />
    ```

Already wired in this PR:

- `frontend/src/views/AthleteProfile.jsx` — `ExportButtons type="athlete"`
  is rendered above the `ProfileHero`.

## 4. Dependencies

`requirements.txt` adds:

```
reportlab>=4.0
openpyxl>=3.1
```

Run `pip install -r requirements.txt` after merging.

## 5. Tests

`tests/test_exports.py` is self-contained and works around the broken
`app.utils.cache` / `app.models.prospect` imports in the current branch by
stubbing them in `sys.modules`. **Once those modules are restored, the
stubs become no-ops and the tests still pass.**

## 6. TODOs / known limitations

- Rankings preset map in `app/api/exports.py::_resolve_preset_weights` is a
  placeholder with three presets (`balanced`, `offense`, `defense`). When
  the real ranking algorithm lands in Phase 4, replace this with a lookup
  against the persisted preset model.
- `_recent_games_for` in both export services only resolves NBA/NHL games
  today (matching `AthleteGameLog` in `app/api/routes.py`). MLB/NFL game
  logs will plug in once those models gain a `Game`-like schema.
- PDF athlete photos: only local filesystem paths are embedded; HTTP URLs
  fall back to the navy-blue initials placeholder so the renderer never
  blocks on a network fetch. Hook into a thumbnail/CDN cache later if
  embedding remote images becomes important.
