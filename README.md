# Pro Sports - Talent Agency

This repository contains a Flask API backend and a React frontend used to manage athlete data for a sports talent agency.

## Backend setup (Flask)

1. **Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Environment variables** – create a `.env` file in the project root and set:
   - `SECRET_KEY` – Flask session secret
   - `DATABASE_URL` – SQLAlchemy database URI
   - `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
   - `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET`
   - `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` and `AZURE_TENANT_ID`
3. **Database migrations**
   ```bash
   flask db upgrade
   ```
4. **Run the server**
   ```bash
   flask run
   ```

## Frontend setup (React)

```bash
cd frontend
npm install
npm run dev
```
The Vite dev server proxies API requests to `http://localhost:5000`, so run the Flask backend first.

## Running tests

Install Python dependencies as above and then install the test packages:
```bash
pip install -r requirements-dev.txt
pytest
```

## User authentication

Local accounts can be created directly in the app. Visit `/auth/register` to
sign up. New users are automatically logged in and assigned the default `viewer`
role. Existing users can log in at `/auth/login` using their username or email
address and password. OAuth logins for Google, GitHub and Microsoft remain
available when configured.

## Docker

A `Dockerfile` and `docker-compose.yml` are provided. To run the app with PostgreSQL using Docker:
```bash
docker-compose up --build
```
This starts the Flask server on port `5000` and a Postgres database on `5432`.


## Supported browsers

The React frontend is regularly tested on the latest versions of Chrome, Firefox, Safari and Edge. Other modern browsers that support ES2015+ features should also work.

## Checking layout on mobile vs. desktop

To verify the responsive design manually:
1. Start the Flask backend with `flask run` and the frontend with `npm run dev`.
2. Open the app in a browser and use developer tools to emulate devices.
3. Test common viewport widths (e.g., 375px and 1280px) and ensure navigation and forms render correctly.

For automated cross-browser or cross-device testing, you can integrate a service like BrowserStack or add Playwright and run `npx playwright test`.

## Documentation

Additional technical documentation is available in the `docs/` directory:

- `database_schema.md` – overview of the database tables and relationships
- `api_endpoints.md` – list of API endpoints with parameters
- `user_guide_athletes.md` – instructions for managing athlete profiles
