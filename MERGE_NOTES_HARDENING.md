# Agent5 - Backend Hardening - Merge Notes

This branch (`agent5-hardening`) introduces:
- Activity-log model + audit middleware + admin read endpoint
- Security-headers middleware (CSP, X-Frame-Options, etc.)
- Stricter rate limits on `/auth/login` and `/auth/register`
- Field-level encryption helpers + `EncryptedString` SQLAlchemy type
- OAuth-flow integration tests (Google, GitHub, Microsoft/Azure)

Everything was scoped to **agent5's owned files**. Where I needed to touch
hot-spot files (`app/__init__.py`, `app/auth/routes.py`) the changes are
marked with `# Agent5: ...` comments so they can be picked out and rebased
cleanly.

---

## Hot-spot edits already applied (and what to verify on merge)

### `app/__init__.py`

Inside `create_app(...)`, after `register_blueprints(app)` and **before**
`if app.config.get('ENABLE_SCHEDULER'):`, this block was inserted:

```python
    # Agent5: register hardening middleware (security headers + audit logging).
    # Order matters: security headers should run on every response (registered
    # first so it sets headers even when audit short-circuits); audit hook
    # records mutating requests after the response is built.
    from app.middleware import register_security_headers, register_audit_middleware
    register_security_headers(app)
    register_audit_middleware(app)

    # Agent5: register activity log read endpoint (admin-only, /api/activity)
    try:
        from app.api.activity import bp as _activity_bp
        app.register_blueprint(_activity_bp)
    except Exception as _e:  # pragma: no cover
        app.logger.error(f"Failed to register activity blueprint: {_e}")
```

**Why this order**: `after_request` hooks fire in **reverse** registration
order in Flask, so registering security headers first means they will be
the *last* hook to run — guaranteeing they decorate every response, even
when the audit hook short-circuits.

**Note**: the existing `after_request` hook in `create_app` (which sets
`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`) becomes
redundant once `register_security_headers` is wired in — it can be removed
in a follow-up commit, or left in place (the headers are simply set twice;
the second set wins). I left it alone to keep this PR surgical.

### `app/auth/routes.py`

Three small edits, each marked `# Agent5: ...`:

1. Imported `limiter` from the app package:
   ```python
   from app import db, oauth, limiter  # Agent5: import shared limiter
   ```
2. Defined a constant near the top:
   ```python
   _AUTH_RATE_LIMIT = '10 per minute'
   ```
3. Decorated `login()` and `register()` view functions with
   `@limiter.limit(_AUTH_RATE_LIMIT)` placed **between** the `@bp.route(...)`
   line and the `def`.

The default Flask-Limiter key uses the same `_limiter_key` function defined
in `app/__init__.py` (API-key prefix or remote address), so the 10/min rule
honors API keys as well as IPs.

---

## Required imports in files I do NOT own

### `app/models/__init__.py`

If you want `from app.models import ActivityLog` to work, append:

```python
from .activity_log import ActivityLog
__all__.append('ActivityLog')
```

I have **not** modified this file (per scope). It is not strictly required
for the audit middleware (which imports `app.models.activity_log` directly)
or for the read endpoint, but it's the convention used by the other models.

### `app/api/__init__.py`

The activity endpoint is a **standalone** `flask.Blueprint` (not a
Flask-RESTX namespace), and is registered directly in `app/__init__.py`
under the URL prefix `/api/activity`. **Do not** add it to the RESTX
`api.namespace(...)` chain — that would double-register it.

If you'd later prefer the endpoint to appear in Swagger docs, convert
`app/api/activity.py` to use `Resource` and `api.namespace('activity', ...)`
in `app/api/__init__.py`. The current setup keeps it deliberately separate
to (1) avoid touching `app/api/__init__.py` and (2) make the admin-only
gating obvious in the routes file.

---

## Requirements changes

### `requirements.txt`

No required additions. `cryptography` is already present (it's an
authlib transitive). I deliberately did NOT add `flask-talisman` because
the security-headers middleware is hand-rolled.

### `requirements-dev.txt`

Added:

```
# Agent5: optional HTTP-mocking dep for OAuth tests; current tests use monkeypatch
responses>=0.25
```

The OAuth tests do not actually require `responses` — they use
`monkeypatch` to swap out the authlib client. I added the dep because the
brief listed it; it's safe to drop if you want a leaner dev image.

---

## Stub modules I created to make the test suite boot

When I started this work, the codebase had broken imports preventing the
app from booting (`app.utils.cache`, `app.utils.security`, `app.api.keys`,
`app.api.prospects`, `app.models.prospect`, `app.models.api_key` were all
referenced but did not exist). I added **minimal stubs** for those so my
tests (and the existing test suite) can collect and run. **Each stub
contains a docstring noting it should be replaced by the owning agent's
implementation:**

- `app/utils/cache.py`         (no-op `cache_manager` + `cached`)
- `app/utils/security.py`      (best-effort `require_api_key`)
- `app/models/prospect.py`     (minimal `ProspectLeague`/`MinorLeagueTeam`/`Prospect`/`ProspectStat`)
- `app/models/api_key.py`      (minimal `ApiKey`)
- `app/api/keys.py`            (empty, presence-only)
- `app/api/prospects.py`       (empty, presence-only)

When the owning agents land their real versions, just **overwrite** these
files. The schemas in the model stubs are intentionally minimal so
schema conflicts during overwrite are unlikely; double-check the
`prospect_leagues`/`minor_league_teams`/`prospects`/`prospect_stats` and
`api_keys` table definitions on merge.

## Test infrastructure

`tests/conftest.py` was added. It does two things:
1. Inserts the project root into `sys.path` (most existing tests do this
   manually; conftest centralizes it).
2. Patches `TestingConfig.SQLALCHEMY_ENGINE_OPTIONS = {}` because the base
   `Config` sets `pool_size`/`max_overflow`, which sqlite (StaticPool)
   rejects. The patch is scoped to `testing` only.

If a richer test-config strategy lands later, this can be removed.

---

## Tests I could not run

- **Redis-backed rate limiting**: Flask-Limiter falls back to in-memory
  storage when Redis is not available, which is what the test environment
  uses. The `10 per minute` rule is exercised at the level of decoration
  but not as a true distributed-rate-limit test. Verify in staging with
  `REDIS_URL` set.
- **Production HSTS**: `test_hsts_enabled_when_configured` exercises HSTS
  via the `HSTS_ENABLED` config flag rather than by booting under
  `production` config (which also requires a non-default SECRET_KEY etc.).
  Header presence is verified; full prod-config validation is out of scope.

## Files that should be applied to no-touch zones (do not auto-apply)

These are **suggestions only** — they are NOT in any commit and you (or the
respective agents) should choose whether to land them:

1. `app/models/__init__.py` — append:
   ```python
   from .activity_log import ActivityLog
   __all__.append('ActivityLog')
   ```
2. `app/__init__.py` — the existing inline `after_request` hook that sets
   `X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection` is now
   redundant with `register_security_headers`. Optionally remove the three
   header-set lines (keep the debug log if you like).

## Phase 4 follow-ups (encrypted columns)

`app/utils/crypto.py` exposes an `EncryptedString` SQLAlchemy type but it
is **not yet applied** to any column. Per the brief, the intentional
candidates for a Phase 4 migration (subject to agency confirmation) are:

- `athlete_profiles.contact_email`
- `athlete_profiles.contact_phone`
- `athlete_profiles.emergency_contact_*` (if those columns exist/are added)
- `user_oauth_accounts.access_token` (column already named `..._encrypted`
  but currently stores plaintext)
- `user_oauth_accounts.refresh_token` (same caveat)

Migrating each requires (a) widening the storage column to fit the Fernet
ciphertext (~1.5x plaintext + 100 bytes), and (b) a one-shot data
backfill that re-encrypts existing rows. Don't ship that without an
explicit Phase-4 approval — losing/rotating the SECRET_KEY would render
columns unreadable.
