# Frontend

This directory contains the React application built with Vite. The app connects to the Flask API in the repository root.

## Development server

Install dependencies once using npm (or yarn):

```bash
cd frontend
npm install
```

Then start the Vite development server:

```bash
npm run dev
```

The server proxies API requests to `http://localhost:5000` so make sure the Flask backend is running locally on port 5000.

## End-to-end tests

Playwright tests are located in the `tests` directory. They spin up the Flask
application in testing mode and drive a headless browser to create and edit an
athlete profile.

To run them:

```bash
# Install Python dependencies
pip install -r ../requirements.txt
# Install browser binaries
playwright install
# Execute tests
pytest tests/test_playwright_e2e.py
```

The server is started automatically by the test suite, so no additional setup is
required.
