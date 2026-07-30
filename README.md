# Pipeline Guardian AI

Pipeline Guardian AI is a local, approval-gated MVP for monitoring failed data-pipeline tasks, retrieving runbooks, producing structured analysis, and dispatching one allowlisted retry.

This repository is safe by default: deterministic fixtures power local tests, live Airflow and Claude calls are opt-in, and recovery cannot run without an operator decision.

## Requirements

- Python 3.11+
- Node.js 24+
- npm

## Backend setup and tests

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests -q
```

## Frontend setup and tests

```bash
cd frontend
npm ci
npm test -- --run
npm run typecheck
npm run build
npx playwright install chromium
npm run e2e
```

## Run the local demo

Start the deterministic backend and frontend in separate terminals:

```bash
# terminal 1, from the repository root
PYTHONPATH=backend .venv/bin/uvicorn app.demo:app --host 127.0.0.1 --port 18000

# terminal 2
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Open <http://127.0.0.1:5173>, then choose **Poll source**. The Vite dev server proxies `/api` to the local FastAPI server on port `18000`.

### Troubleshooting `ERR_CONNECTION_REFUSED`

`127.0.0.1` is the computer running the browser. Both terminals must remain open on that same computer. If the page says it refused the connection, restart the frontend command and confirm it prints `Local: http://127.0.0.1:5173/`; then refresh the page. If the page loads but polling fails, restart the backend command and confirm `http://127.0.0.1:18000/docs` opens. Port `8000` is intentionally avoided because it is commonly used by other local services.

## Runtime configuration

Set runtime values in your local shell or an ignored `.env` file. Never commit credentials. The v0.1 runtime accepts a loopback SQLite database and loopback Airflow URL. Claude analysis requires the provider key and exact model identifier; missing or invalid values fail closed as `analysis_failed`. No provider credentials are needed for the test suite.

## Scope

Included: one normalized source adapter, failed-task detection, SQLite FTS5 runbook retrieval, structured analysis boundary, approval/rejection, one idempotent retry, verification, audit history, and a single operator page.

Not included: multi-tenant production auth, cloud deployment, Kafka, vector embeddings, arbitrary code or SQL execution, notifications, or autonomous remediation without approval.

## Project layout

`backend/app` contains the API and domain services. `backend/tests` contains deterministic acceptance coverage. `frontend/src` contains the operator page. No files outside this repository are required.

## License

MIT. See [LICENSE](LICENSE).
