# Backend: Integration Health Monitor (FastAPI)

Rule-based health checks over third-party integration request logs.
Storage is currently **JSON files on disk**: each uploaded log file is saved in
`data/uploads/` (with an `index.json` of metadata) and survives restarts. Nothing is
preloaded; the client uploads files first. Each file is analysed on its own.
MongoDB will replace `FileStore` later. No other layer changes.

## Run

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

- Swagger UI: http://localhost:8000/docs
- Tests: `.venv\Scripts\python -m pytest -q` (tests use their own copy of the starter data in `tests/fixtures/`)

## Layout

```
app/
  main.py                 FastAPI app, CORS, error handlers, file store setup
  config.py               env settings + health_config.yaml policy
  domain.py               LogRecord, status constants, integration ids
  schemas.py              Pydantic input validation + typed responses
  deps.py                 shared repo / policy / time window
  routers/                system, dashboard, integrations, logs (upload)
  services/
    ingestion_service.py  validate -> UTC -> fingerprint -> dedupe
    metrics_service.py    N=S+E+T, rates, avg/p95 success latency
    health_engine.py      thresholds -> healthy/degraded/critical/unknown
    failure_analyzer.py   dominant failure + recommendations
    recommendation_engine.py  signal -> possible cause + next step
    time_window.py        window parsing, historical demo mode
    health_service.py     orchestrates the pipeline
  repositories/
    log_repository.py     LogRepository protocol + InMemoryLogRepository
health_config.yaml        thresholds and per-integration latency SLOs
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | backend liveness + number of files |
| GET | `/api/files` | uploaded files, newest first |
| POST | `/api/files` | upload a JSON file (409 if already uploaded, 422 if no valid rows) |
| DELETE | `/api/files/{file_id}` | delete a file; returns `remaining` and `latest_file_id` |
| GET | `/api/dashboard?file_id=&window=1h` | KPI summary, needs attention, table |
| GET | `/api/integrations?file_id=&window=1h` | all integration results, worst first |
| GET | `/api/integrations/{id}?file_id=&window=1h` | metrics, rules, reasons, recommendations |
| GET | `/api/integrations/{id}/logs?file_id=&status=failures&page=1` | raw logs, newest first |
| GET | `/api/integrations/{id}/trends?file_id=&window=1h` | requests and avg latency per time bucket |
| GET | `/api/config/thresholds` | current policy |

`file_id` is optional and defaults to the most recent file (404 if none uploaded).
Upload and delete need header `X-Admin-Token` only if `ADMIN_TOKEN` is set.

`window`: `15m, 30m, 1h, 6h, 24h, 7d, all`. Window semantics: `start < timestamp <= end`.
In demo mode, `end` = latest log timestamp.

## Environment variables

| Name | Default | Meaning |
|---|---|---|
| `DEMO_MODE` | `true` | reference time = latest log instead of wall clock |
| `FRONTEND_URL` | `http://localhost:5173` | allowed CORS origin |
| `ADMIN_TOKEN` | unset | if set, required for uploads |
| `UPLOADS_DIR` | `data/uploads` | where uploaded files are stored |
| `HEALTH_CONFIG` | `health_config.yaml` | policy file |
| `MAX_UPLOAD_BYTES` | `1000000` | upload size limit |

## Expected results (starter file uploaded, window=1h)

| Integration | Health | Failure % | Dominant |
|---|---|---|---|
| ADP Payroll Sync | critical | 41.67 | HTTP 500 |
| Greenhouse ATS Sync | critical | 50.00 | timeout |
| DocuSign Envelope API | degraded | 33.33 | HTTP 429 |
| Workday Directory Sync | healthy | 8.33 | HTTP 503 |
| Slack Notifications | healthy | 8.33 | HTTP 500 |

Totals: 60 requests, 17 failures, 28.33%. The starter `compute_error_rate` ignores
timeouts and reports Greenhouse at 14.29%; this backend counts them (50%).
