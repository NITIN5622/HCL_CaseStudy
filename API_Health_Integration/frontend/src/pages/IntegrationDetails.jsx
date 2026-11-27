import { useState } from "react";
import { ArrowLeft, CheckCircle2, MinusCircle, XCircle } from "lucide-react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { LatencyChart, StatusTimelineChart } from "../components/Charts.jsx";
import HealthBadge from "../components/HealthBadge.jsx";
import LogTable from "../components/LogTable.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
import SummaryCard from "../components/SummaryCard.jsx";
import WindowBar from "../components/WindowBar.jsx";
import { api } from "../services/api.js";
import { ms, pct, utc } from "../services/format.js";
import { useApi } from "../services/useApi.js";

const RULE_STYLE = {
  critical: { Icon: XCircle, cls: "text-red-600" },
  degraded: { Icon: XCircle, cls: "text-amber-600" },
  ok: { Icon: CheckCircle2, cls: "text-emerald-600" },
  skipped: { Icon: MinusCircle, cls: "text-slate-400" },
};

function Section({ title, children }) {
  return (
    <section className="space-y-3">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">{title}</h2>
      {children}
    </section>
  );
}

export default function IntegrationDetails() {
  const { id } = useParams();
  const [params, setParams] = useSearchParams();
  const window = params.get("window") || "1h";
  const fileId = params.get("file");
  const [logFilter, setLogFilter] = useState("");
  const [page, setPage] = useState(1);

  const detail = useApi(() => api.integration(fileId, id, window), [fileId, id, window]);
  const trends = useApi(() => api.integrationTrends(fileId, id, window), [fileId, id, window]);
  const logs = useApi(
    () => api.integrationLogs(fileId, id, { window, status: logFilter, page, pageSize: 12 }),
    [fileId, id, window, logFilter, page]
  );

  const refresh = () => {
    detail.reload();
    trends.reload();
    logs.reload();
  };
  const d = detail.data;
  const m = d?.metrics;

  return (
    <div className="space-y-6">
      <Link to={`/dashboard?${fileId ? `file=${fileId}&` : ""}window=${window}`} className="inline-flex items-center gap-1 text-sm text-indigo-600 hover:underline">
        <ArrowLeft size={14} /> Back to dashboard
      </Link>

      {detail.error && <ErrorState error={detail.error} onRetry={detail.reload} />}
      {detail.loading && !d && <Loading text="Loading integration…" />}

      {d && (
        <>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-xl font-semibold text-slate-900">{d.name}</h1>
            <HealthBadge health={d.health} size="lg" />
            <span className="text-xs text-slate-500">
              <span className="capitalize">{d.tier}</span> tier · latency SLO {ms(d.latency_slo_ms)}
            </span>
          </div>

          <WindowBar
            windowInfo={d.window}
            value={window}
            onChange={(w) => {
              setPage(1);
              setParams(fileId ? { file: fileId, window: w } : { window: w });
            }}
            onRefresh={refresh}
            loading={detail.loading}
          />

          {/* Block B: metrics */}
          <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <SummaryCard label="Requests" value={m.total_requests} />
            <SummaryCard label="Successes" value={m.successes} tone="healthy" />
            <SummaryCard label="Errors" value={m.errors} tone={m.errors ? "critical" : "default"} />
            <SummaryCard label="Timeouts" value={m.timeouts} tone={m.timeouts ? "critical" : "default"} />
            <SummaryCard label="Failure rate" value={pct(m.failure_rate)} hint="(errors + timeouts) / requests" />
            <SummaryCard label="Timeout rate" value={pct(m.timeout_rate)} />
            <SummaryCard label="Avg latency" value={ms(m.avg_latency_ms)} hint={`P95 ${ms(m.p95_latency_ms)} · successful only`} />
            <SummaryCard label="Last success" value={utc(m.last_success)} hint={m.last_success ? "UTC" : "none in window"} />
          </section>

          {/* Block E: charts */}
          {trends.data && (
            <section className="grid gap-4 lg:grid-cols-2">
              <StatusTimelineChart trends={trends.data} />
              <LatencyChart trends={trends.data} slo={d.latency_slo_ms} />
            </section>
          )}

          <div className="grid gap-6 lg:grid-cols-2">
            {/* Block C: why this status */}
            <Section title="Why this status">
              <ul className="divide-y divide-slate-100 rounded-xl border border-slate-200 bg-white">
                {d.rules.map((r) => {
                  const st = RULE_STYLE[r.severity];
                  return (
                    <li key={r.rule} className="flex items-start gap-3 px-4 py-3 text-sm">
                      <st.Icon size={18} className={`mt-0.5 shrink-0 ${st.cls}`} />
                      <span className="text-slate-700">{r.message}</span>
                    </li>
                  );
                })}
              </ul>
            </Section>

            {/* Block D: failure breakdown + recommendation */}
            <Section title="Failure breakdown & next steps">
              {d.recommendations.length === 0 ? (
                <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-500">
                  No failures in this window.
                </div>
              ) : (
                <ul className="space-y-3">
                  {d.recommendations.map((r) => (
                    <li key={r.signal} className="rounded-xl border border-slate-200 bg-white p-4 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-900">
                          {r.signal === "high_latency" ? "High latency" : r.signal === "no_data" ? "No requests" : r.signal}
                        </span>
                        {r.signal !== "high_latency" && r.signal !== "no_data" && (
                          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium tabular-nums">
                            {r.count}×{r.signal === d.dominant_failure ? " · dominant" : ""}
                          </span>
                        )}
                      </div>
                      <p className="mt-1 text-slate-600">
                        <span className="text-slate-500">Possible cause:</span> {r.possible_cause}
                      </p>
                      <p className="mt-0.5 text-slate-800">
                        <span className="text-slate-500">Next step:</span> {r.next_step}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
              <p className="text-xs text-slate-400">Possible causes guide investigation; they are not confirmed root causes.</p>
            </Section>
          </div>

          {/* Block F: raw logs */}
          <Section title="Request logs">
            <div className="flex gap-2">
              {[
                ["", "All"],
                ["failures", "Failures only"],
              ].map(([v, label]) => (
                <button
                  key={label}
                  onClick={() => {
                    setLogFilter(v);
                    setPage(1);
                  }}
                  className={`rounded-lg px-3 py-1.5 text-sm ring-1 ${
                    logFilter === v ? "bg-indigo-600 text-white ring-indigo-600" : "bg-white ring-slate-300 hover:bg-slate-50"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
            {logs.error && <ErrorState error={logs.error} onRetry={logs.reload} />}
            {logs.data && <LogTable page={logs.data} onPage={setPage} />}
          </Section>
        </>
      )}
    </div>
  );
}
