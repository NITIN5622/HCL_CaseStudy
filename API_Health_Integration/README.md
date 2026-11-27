# Integration Health Monitor

**Brightline HR · Case Study 4**

Brightline HR connects to payroll, e-signature, ATS, directory-sync and notification
providers. Broken integrations were found only when customers filed support tickets,
often days later. This app turns raw request logs into a morning health check. It shows
which integrations are **healthy, degraded, critical or unknown**, **why**, and **what to
check next**.

Health is decided by clear, configurable rules, not ML, so every status can be explained.

---

## Features

- **Upload page:** upload JSON log files and see the existing files and their count.
  **Continue** is enabled once at least one file exists.
- **Dashboard:** one uploaded file at a time; it opens on the most recent one.
  - Upload logs, file selector, delete file, time window (15m to all data)
  - KPI cards: healthy / degraded / critical / unknown, total requests, overall failure rate
  - Needs Attention: problem integrations first, each with its reason and next step
  - Charts: failure rate per integration (with threshold lines), and successes /
    errors / timeouts per integration
  - Integration table: click a row to open its details
- **Integration details:** metric cards, requests-over-time and latency charts,
  "Why this status" (every rule with its value and threshold), failure breakdown with
  possible cause and next step, and paginated raw logs (all or failures only).
- **Deleting files:**
  - deleting the file being viewed switches to the most recent remaining file;
  - deleting the last file returns to the upload page.
- **Import validation:**
  - invalid rows are rejected and listed by row number;
  - duplicate rows are skipped;
  - the same file uploaded twice is refused.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, Recharts, React Router, Lucide icons |
| Backend | Python, FastAPI, Pydantic, Uvicorn |
| Storage | JSON files on disk (`backend/data/uploads/`); MongoDB planned |
| Config | `backend/health_config.yaml` (thresholds and latency SLOs) |
| Tests | Pytest (52 tests) |

---

## Project structure

```
API -Health-Integration/
├── backend/
│   ├── app/
│   │   ├── main.py              FastAPI app, CORS, error handling
│   │   ├── config.py            settings + health policy loader
│   │   ├── domain.py            LogRecord and status constants
│   │   ├── schemas.py           Pydantic validation and response models
│   │   ├── deps.py              shared dependencies (selected file, window)
│   │   ├── routers/             files, dashboard, integrations, system
│   │   ├── services/            ingestion, metrics, health engine,
│   │   │                        failure analyzer, recommendations, trends
│   │   └── repositories/        file_store.py (uploaded files),
│   │                            log_repository.py (in-memory logs per file)
│   ├── data/uploads/            uploaded files (created automatically)
│   ├── tests/                   pytest suite + fixtures/integration_logs.json
│   ├── health_config.yaml
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/               UploadPage, Dashboard, IntegrationDetails
│       ├── components/          charts, tables, modals, badges, cards
│       └── services/            API client, formatting helpers
├── sample_logs/                 two ~500-row sample log files
└── ARCHITECTURE.txt             architecture write-up
```

---

## Getting started (Windows / PowerShell)

### Do I need to download anything?

- **On the machine where this was built:** no. All libraries are already installed in
  `backend\.venv` (Python) and `frontend\node_modules` (JavaScript). Just start the two
  servers (the last command in each block below).
- **On a new computer:** yes, once.
  1. Install two free programs:
     - **Python 3.11+** from https://www.python.org/downloads/ (tick "Add Python to PATH")
     - **Node.js 20+** from https://nodejs.org/
  2. Install the project's libraries with the commands below. `requirements.txt` and
     `package.json` pin the exact versions, so every machine gets the same setup.

  A copied `.venv` folder does **not** work on another computer, because it stores paths
  from the original machine. Always recreate it.

Check the programs are installed:

```powershell
python --version
node --version
```

Then use two terminals.

### 1. Backend (terminal 1)

```powershell
cd "C:\Users\nitin\Downloads\API -Health-Integration\backend"
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

The first three lines are a one-time setup. After that, only the `cd` and the last line
are needed. Always start the backend from inside `backend`.

- API docs (Swagger): http://localhost:8000/docs

### 2. Frontend (terminal 2)

```powershell
cd "C:\Users\nitin\Downloads\API -Health-Integration\frontend"
npm install
npm run dev
```

`npm install` is only needed the first time.

- App: **http://localhost:5173/** (upload page)

To stop either server, press **Ctrl + C** in its terminal.

### Common problems

| Problem | Fix |
|---|---|
| `The module '.venv' could not be loaded` or `No module named app` | You are not inside `backend`. Run `cd backend` first. |
| `address already in use` on port 8000 | Another backend is running. Stop it with Ctrl + C, or free the port: `Get-NetTCPConnection -LocalPort 8000 -State Listen \| Select-Object -ExpandProperty OwningProcess -Unique \| ForEach-Object { Stop-Process -Id $_ -Force }` |
| Dashboard says "Cannot reach the backend" | The backend isn't running on port 8000. Start it (terminal 1). |
| `Activate.ps1 cannot be loaded because running scripts is disabled` | You don't need to activate. Use `.venv\Scripts\python ...` as shown, or run `Set-ExecutionPolicy -Scope Process RemoteSigned` first. |

---

## Sharing the project

When you zip the folder or push it to GitHub, **leave out**:

| Folder | Why |
|---|---|
| `backend\.venv` | large and specific to this machine; recreated by `pip install` |
| `frontend\node_modules` | large; recreated by `npm install` |
| `backend\data\uploads` | your uploaded files (private data) |

`.gitignore` already excludes these from Git. The other person follows
**Getting started** above to install everything.

---

## Using the app

1. Open http://localhost:5173/ and upload a log file. Use
   `backend/tests/fixtures/integration_logs.json` (the starter data) or a file in `sample_logs/`.
2. Click **Continue to dashboard**.
3. Read **Needs Attention**, then click an integration to see the evidence.
4. Use the file selector to compare files, and the time window to zoom in or out.

### Log file format

```json
{
  "logs": [
    {"integration": "Slack Notifications", "timestamp": "2026-08-04T09:00:00",
     "status": "success", "status_code": 200, "latency_ms": 130}
  ]
}
```

- `status` is `success`, `error` or `timeout`.
- `status_code` may be `null` for timeouts.
- Timestamps without a timezone are treated as UTC.

---

## How health is decided

Metrics are computed per integration in the selected time window
(N = successes + errors + timeouts):

| Rule | Degraded | Critical |
|---|---|---|
| Failure rate: (errors + timeouts) / N | ≥ 10% | ≥ 40% |
| Timeout rate: timeouts / N | ≥ 5% | ≥ 20% |
| Avg latency of successful requests | ≥ SLO | ≥ 2 × SLO |

The latency SLO is set per integration:

| Integration | SLO |
|---|---|
| Slack, Workday | 500 ms |
| ADP, Greenhouse, any other integration | 1000 ms |
| DocuSign | 1500 ms |

Status is decided in this order:
1. **Unknown** if fewer than 5 requests.
2. **Critical** if any rule reaches its critical threshold.
3. **Degraded** if any rule reaches its degraded threshold.
4. **Healthy** otherwise.

All rules are evaluated and shown, not just the first one that fails. Thresholds are
starting proposals, to be validated with Platform Ops, and can be changed in
`health_config.yaml` without code changes.

**Failure signals mapped to a possible cause:**
- **429:** rate limiting on our side.
- **401 / 403:** authentication or permission problem.
- **500 / 503:** provider error or unavailability.
- **Timeout:** connectivity or provider slowness.

These are possible causes to guide investigation, not confirmed root causes.

### Bug found in the starter code

`compute_error_rate()` in the provided `integration_utils.py` only counts `success` and
`error` rows, so timeouts are silently dropped. As a result:
- Greenhouse shows **14.29%** instead of the real **50%**, and the worst integration looks almost healthy.
- `average_latency_ms()` also hides the 30-second timeouts.

This app counts timeouts as failures.

### Expected results: starter file, last 1h

| Integration | Health | Failure rate | Main failure |
|---|---|---|---|
| ADP Payroll Sync | Critical | 41.67% | HTTP 500 |
| Greenhouse ATS Sync | Critical | 50.00% | timeout |
| DocuSign Envelope API | Degraded | 33.33% | HTTP 429 |
| Workday Directory Sync | Healthy | 8.33% | HTTP 503 |
| Slack Notifications | Healthy | 8.33% | HTTP 500 |

Total: 60 requests, 17 failures, 28.33%.

---

## Sample log files (`sample_logs/`)

| File | Story (last 1h) |
|---|---|
| `logs_2026-08-11_payroll_incident.json` (500 rows) | ADP critical (HTTP 500 incident); DocuSign degraded (429 bursts); Workday degraded by **latency only** (0% failures) |
| `logs_2026-08-12_slack_outage.json` (495 rows) | Slack critical (503 outage); Workday degraded (401 expired token); BambooHR **unknown** (3 requests); includes 4 invalid rows, 3 duplicates, shuffled order |

---

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/files` | uploaded files, newest first |
| POST | `/api/files` | upload a file |
| DELETE | `/api/files/{file_id}` | delete a file |
| GET | `/api/dashboard?file_id=&window=1h` | summary, needs attention, table |
| GET | `/api/integrations/{id}?file_id=&window=` | details, rules, recommendations |
| GET | `/api/integrations/{id}/logs?file_id=&status=failures` | raw logs (paginated) |
| GET | `/api/integrations/{id}/trends?file_id=&window=` | time-bucketed counts and latency |
| GET | `/api/config/thresholds` | current health policy |
| GET | `/api/health` | backend liveness |

`file_id` defaults to the most recent file. Full interactive docs are at `/docs`.

---

## Tests

```powershell
cd backend
.venv\Scripts\python -m pytest -q
```

The tests cover:
- metrics, including timeouts counted as failures and null rates when there's no data;
- exact threshold boundaries and status precedence;
- import validation and duplicate handling;
- file upload, selection, deletion and persistence across restarts;
- all five expected classifications on the starter data.

---

## Design decisions

- **Rules, not ML:** small data, no labelled incidents, and ops must be able to see *why*.
- **Health computed live, never stored:** it depends on the selected window and the policy.
- **Unknown instead of Healthy** when data is thin: no data is not evidence of health.
- **Historical demo mode:** "now" is the latest log in the file, so old sample data still
  shows a meaningful "last 1h".
- **Repository layer:** only `file_store.py` knows where data lives, so moving to MongoDB
  replaces one class.

## Limitations and next steps

- Storage is JSON on disk, which suits a single-client demo. **Next: MongoDB.**
- No login. If `ADMIN_TOKEN` is set, upload and delete require the `X-Admin-Token` header.
- Thresholds are global proposals; per-tier thresholds and learned baselines come later.
- No scheduled 7 AM report or Slack/email alerts yet.
- Duplicate rows are detected by content, because the logs have no request ID.
