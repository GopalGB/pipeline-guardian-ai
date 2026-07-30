# Pipeline Guardian AI

Pipeline Guardian AI is a local, approval-gated MVP for monitoring failed data-pipeline tasks, retrieving runbooks, producing structured analysis, and dispatching one allowlisted retry.

This repository is safe by default: deterministic fixtures power local tests, live Airflow and Claude calls are opt-in, and recovery cannot run without an operator decision.

## Requirements

- Python 3.11+
- Node.js 20+
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

## Runtime configuration

Set runtime values in your local shell or an ignored `.env` file. Never commit credentials. The v0.1 runtime accepts a loopback SQLite database and loopback Airflow URL. Claude analysis requires the provider key and exact model identifier; missing or invalid values fail closed as `analysis_failed`. No provider credentials are needed for the test suite.

## Scope

Included: one normalized source adapter, failed-task detection, SQLite FTS5 runbook retrieval, structured analysis boundary, approval/rejection, one idempotent retry, verification, audit history, and a single operator page.

Not included: multi-tenant production auth, cloud deployment, Kafka, vector embeddings, arbitrary code or SQL execution, notifications, or autonomous remediation without approval.

## Project layout

`backend/app` contains the API and domain services. `backend/tests` contains deterministic acceptance coverage. `frontend/src` contains the operator page. No files outside this repository are required.

## License

MIT. See [LICENSE](LICENSE).
