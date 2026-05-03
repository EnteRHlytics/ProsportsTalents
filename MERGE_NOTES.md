# Merge Notes — Agent 2 (search + saved searches)

These are the surgical changes the integrator needs to apply at merge
time to wire the new search UI and saved-searches feature into the
shared, conflict-prone files. Each diff is isolated to a single file
so it is easy to apply by hand.

---

## 1. `app/api/__init__.py`

Register the new saved-searches API module so its routes get attached
to the Flask-RESTX `Api`. Add `saved_searches` to the existing import
list at the bottom of the file:

```diff
-from app.api import routes, athletes, skills, rankings, keys, prospects  # noqa: E402
+from app.api import routes, athletes, skills, rankings, keys, prospects, saved_searches  # noqa: E402
```

No other changes are needed — the new module attaches its routes
directly to the shared `api` object via `@api.route(...)`.

---

## 2. `app/models/__init__.py`

Export the new `SavedSearch` model. Add the import + `__all__` entry
near the bottom of the file (after the existing model imports):

```diff
+from .saved_search import SavedSearch
+
+__all__.append('SavedSearch')
```

The reverse `User.saved_searches` collection is wired automatically
via the `backref` declared on `SavedSearch.user`, so no edit to
`app/models/user.py` is required.

---

## 3. `frontend/src/App.jsx`

Replace the existing `/discover` route (which currently points at the
legacy `AthleteList` component) so it renders the new `Discover`
view. Apply both edits:

```diff
-import AthleteList from './components/AthleteList';
+import Discover from './views/Discover';
```

```diff
-            <Route path="/discover" element={<AthleteList />} />
+            <Route path="/discover" element={<Discover />} />
```

If you would rather keep the old list available, mount it at a
different path (e.g. `/discover/legacy`) instead of removing it
outright.

---

## 4. (Already created) `migrations/versions/a2c4e1d9b0f5_add_saved_searches.py`

This migration is wired with `down_revision = 'f29d5d6ebc1b'` (the
current alembic head at branch creation time). If another agent
adds a migration that bumps the head before this branch lands,
re-point `down_revision` to the new head and regenerate the
`revision` id with `flask db revision --rebase` (or just edit the
constant by hand).

---

## 5. Heads-up on missing infra (not owned by Agent 2)

While building this branch we discovered several import-time issues
that block ALL existing tests, not just this branch:

- `app/utils/cache.py` was missing — `app/utils/__init__.py` imports
  `cache_manager` and `cached` from it, which prevented every test
  module from collecting. **Agent 2 added a minimal stub** at
  `app/utils/cache.py` (no-op cache, no-op `@cached` decorator) so
  the app boots in test environments. If another agent has a real
  Redis-backed implementation, that file should win at merge.
- `app/models/__init__.py` imports `prospect` and `api_key` modules
  that do not yet exist on this branch. Agent 2 sidestepped this in
  its own test module by injecting `sys.modules` stubs before
  importing the app — see the top of `tests/test_saved_searches.py`.
  Once the prospect / api_key agents land their code, those stubs
  become unnecessary but remain harmless.
- `config.Config.SQLALCHEMY_ENGINE_OPTIONS` includes `pool_size` /
  `max_overflow`, which SQLite rejects. The fixture in
  `tests/test_saved_searches.py` works around this by zeroing the
  options on the `Config` class for the duration of the test. Long
  term it would be cleaner to push that override into
  `config.TestingConfig` directly.

---

## 6. Frontend `useApi` hook

`Discover.jsx` was supposed to consume a shared `useApi` hook from
`frontend/src/hooks/useApi.js`. That directory does not exist on
this branch, so `Discover.jsx` ships with a tiny inline `apiRequest`
helper. When the FE-Foundation agent lands `useApi`, the helper at
the top of `Discover.jsx` can be removed and call sites updated 1:1
— there are five call sites, all named `apiRequest(...)`.

Likewise, the search components do **not** depend on
`context/AuthContext` or any layout component owned by Agent 1, so
they slot in cleanly regardless of FE-Foundation merge order.
