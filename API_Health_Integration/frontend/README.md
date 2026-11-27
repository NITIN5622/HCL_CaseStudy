# Frontend: Integration Health Monitor (React + Vite + Tailwind)

Display only. All health logic lives in the backend.

## Run

```powershell
cd frontend
npm install
npm run dev
```

Opens on http://localhost:5173. Expects the backend at `http://localhost:8000`
(override with `VITE_API_BASE_URL` in `.env`).

## Pages

- `/` Upload page: upload logs, dropdown of existing files with a count, and
  **Continue** (enabled once at least 1 file exists; opens the most recent file)
- `/dashboard?file=&window=` Dashboard: Upload logs, file selector, Delete file, time window;
  KPI cards, Needs Attention, failure-rate and outcome charts, integration table.
  Deleting the viewed file switches to the most recent remaining file; deleting the last
  file returns to the upload page.
- `/integrations/:id?file=&window=` Details: metric cards, requests-over-time and latency charts,
  why this status (every rule), failure breakdown with next steps, request logs

The selected file and time window live in the URL, so they survive navigation and refresh.
Chart colours (success / error / timeout) were checked with the dataviz palette validator.
