# Pro Sports Talents

Flask API backend + React (Vite) frontend for a sports talent agency managing athlete profiles across NBA, NFL, MLB, NHL, and Soccer.

---

## Backend setup (Flask)

### 1. Python environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # for tests
```

### 2. Environment variables
Create a `.env` file in the project root:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Flask session secret |
| `DATABASE_URL` | SQLAlchemy database URI (default: PostgreSQL) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth (optional) |
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | GitHub OAuth (optional) |
| `AZURE_CLIENT_ID` / `AZURE_CLIENT_SECRET` / `AZURE_TENANT_ID` | Microsoft OAuth (optional) |
| `BALLDONTLIE_API_TOKEN` | BallDontLie API (covers NBA + NFL) |
| `NBA_API_TOKEN` | NBA-specific override |
| `NFL_API_TOKEN` | NFL-specific override |
| `NBA_API_BASE_URL` | Default: `https://api.balldontlie.io/v1` |
| `NFL_API_BASE_URL` | Default: `https://api.balldontlie.io/nfl/v1` |
| `MLB_API_BASE_URL` | Default: `https://statsapi.mlb.com/api/v1` |
| `NHL_API_BASE_URL` | Default: `https://statsapi.web.nhl.com/api/v1` |
| `ENABLE_SCHEDULER` | Set to `true` to activate background sync jobs |
| `REDIS_URL` | Rate-limit storage (default: `redis://localhost:6379`) |

### 3. Initialize the database
```bash
flask db upgrade   # apply all migrations
flask init-db      # seed default roles, sports, and positions
flask seed-demo    # insert demo athletes (optional)
```

### 4. Run the server
```bash
flask run          # dev server on http://localhost:5000
```

### 5. Scheduled jobs (optional)
Set `ENABLE_SCHEDULER=true` in `.env` to enable APScheduler:
- **Nightly 2 AM** — sync game results
- **Weekly Sunday 3 AM** — sync player stats

---

## Frontend setup (React)

The Vite dev server runs on **http://localhost:5173** and proxies all `/api/*` requests to `http://localhost:5000`. Start the Flask backend before starting the frontend.

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

### Routes

| Path | View |
|---|---|
| `/` | Dashboard — KPI cards, featured athletes, top rankings |
| `/discover` | Athlete list with search and sport/position/team/age filters |
| `/compare` | Side-by-side athlete comparison |
| `/athletes/new` | Create a new athlete profile |
| `/athletes/:id` | Full athlete profile (stats, skills, media, game log) |
| `/athletes/:id/edit` | Edit an existing athlete profile |

### Navigation
The top navbar shows links based on the current user's role:

| Role | Accessible sections |
|---|---|
| `admin` / `agency_admin` | Dashboard, Discover, Compare, Admin |
| `agent` | Dashboard, Discover, Compare |
| `scout` | Dashboard, Discover, Compare |
| `athlete` | Dashboard |
| `viewer` | Dashboard, Discover |

---

## Running tests

### Backend
```bash
pytest              # all tests
pytest tests/test_api.py
pytest -k "test_name"
```

### Frontend
```bash
cd frontend
npm test            # vitest
```

Test files live in `frontend/tests/`. Vitest runs in jsdom mode with `@testing-library/react`.

---

## Running CI locally

The same checks GitHub Actions runs on every push and pull request can be run locally:

```bash
# 1. Python lint (ruff)
pip install -r requirements-dev.txt
ruff check .                # report only
ruff check . --fix          # apply auto-fixes

# 2. Backend tests
pytest tests/ -q --tb=short

# 3. Frontend lint (eslint)
cd frontend
npm install
npm run lint                # eslint src

# 4. Frontend build + tests (vitest, includes a11y checks)
npm run build
npm test -- --run
```

The CI workflow lives in `.github/workflows/ci.yml` and runs three jobs in parallel:
`lint` (ruff + eslint), `backend` (pytest on Python 3.11 and 3.12 with a Postgres
service container), and `frontend` (vite build + vitest). Lint config lives in
`pyproject.toml` (`[tool.ruff]`) and `frontend/.eslintrc.cjs`. Accessibility is
covered by `frontend/tests/a11y.test.jsx`, which mounts the Dashboard and asserts
zero serious/critical axe-core violations.

---

## User authentication

- Register at `/auth/register` — new accounts receive the `viewer` role automatically.
- Log in at `/auth/login` with username/email and password.
- OAuth logins (Google, GitHub, Microsoft) are available when the corresponding env vars are configured.

---

## Docker

```bash
docker-compose up --build
```

Starts the Flask server on port `5000` and a PostgreSQL database on port `5432`.

---

## API

Swagger UI is available at **http://localhost:5000/api/swagger**.

API endpoints accept an `X-API-Key` header. Keys are managed via `/api/keys`. Rate limiting buckets are keyed on the first 12 characters of the API key, falling back to IP address.

---

## Architecture overview

```
ProsportsTalents/
├── app/
│   ├── __init__.py        # Application factory
│   ├── models/            # SQLAlchemy models (User, AthleteProfile, Stats, …)
│   ├── api/               # Flask-RESTX REST API blueprint (/api)
│   ├── auth/              # Auth blueprint (/auth) — local + OAuth
│   ├── athletes/          # Athlete profile pages blueprint
│   ├── services/          # Business logic & external API clients
│   ├── scheduler.py       # APScheduler setup
│   └── jobs.py            # Scheduled job definitions
├── frontend/
│   ├── src/
│   │   ├── App.jsx        # Router root
│   │   ├── views/         # Page-level components
│   │   ├── components/    # Reusable UI components
│   │   ├── context/       # AuthContext (role-based permissions)
│   │   ├── hooks/         # useApi and other hooks
│   │   └── utils/         # Formatters, sport config, stat helpers
│   └── tests/             # Vitest unit/component tests
├── config.py              # Dev / Prod / Testing config classes
├── run.py                 # Entry point + CLI commands
└── docker-compose.yml
```

## Supported browsers

Tested on the latest versions of Chrome, Firefox, Safari, and Edge. Any modern browser supporting ES2015+ should work.
