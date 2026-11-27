import { useEffect, useState } from "react";
import { FileText, Trash2, Upload } from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { FailureRateChart, OutcomeMixChart } from "../components/Charts.jsx";
import { DeleteModal, UploadModal } from "../components/FileModals.jsx";
import IntegrationTable from "../components/IntegrationTable.jsx";
import NeedsAttention from "../components/NeedsAttention.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
import SummaryCard from "../components/SummaryCard.jsx";
import WindowBar from "../components/WindowBar.jsx";
import { api } from "../services/api.js";
import { fileLabel, pct } from "../services/format.js";
import { useApi } from "../services/useApi.js";

const btn = "inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-50";

export default function Dashboard() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const window = params.get("window") || "1h";
  const fileParam = params.get("file");
  const [modal, setModal] = useState(null); // "upload" | "delete" | null

  const files = useApi(() => api.listFiles(), []);
  const thresholds = useApi(() => api.thresholds(), []);
  const list = files.data || [];

  // Which file is shown: the one in the URL if it still exists, else the most recent.
  const fileId = list.some((f) => f.id === fileParam) ? fileParam : list[0]?.id;

  useEffect(() => {
    if (!files.data) return;
    if (files.data.length === 0) navigate("/", { replace: true }); // nothing left -> upload page
    else if (fileId !== fileParam) setParams({ file: fileId, window }, { replace: true });
  }, [files.data, fileId, fileParam, window, navigate, setParams]);

  const dash = useApi(() => (fileId ? api.dashboard(fileId, window) : Promise.resolve(null)), [fileId, window]);
  const data = dash.data;
  const s = data?.summary;

  const selectFile = (id) => setParams({ file: id, window });

  const onUploaded = (info) => {
    setModal(null);
    files.reload();
    selectFile(info.id); // newest upload becomes the current file
  };

  const onDeleted = (deletedId, result) => {
    setModal(null);
    if (result.remaining === 0) return navigate("/", { replace: true });
    if (deletedId === fileId) selectFile(result.latest_file_id);
    files.reload();
  };

  const t = thresholds.data;
  const chartThresholds = t
    ? [
        { value: t.failure_degraded, label: `${t.failure_degraded}%`, color: "#d97706" },
        { value: t.failure_critical, label: `${t.failure_critical}%`, color: "#dc2626" },
      ]
    : [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Integration health</h1>
          <p className="text-sm text-slate-500">Which integrations need attention, and why.</p>
        </div>

        {/* File controls: upload, select file, delete */}
        <div className="flex flex-wrap items-center gap-2">
          <button onClick={() => setModal("upload")} className={btn}>
            <Upload size={14} /> Upload logs
          </button>
          <label className="sr-only" htmlFor="file-select">Log file</label>
          <div className="relative">
            <FileText size={14} className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <select
              id="file-select"
              value={fileId || ""}
              onChange={(e) => selectFile(e.target.value)}
              className="max-w-[22rem] rounded-lg border border-slate-300 bg-white py-1.5 pl-8 pr-2 text-sm"
            >
              {list.map((f, i) => (
                <option key={f.id} value={f.id}>
                  {fileLabel(f)}{i === 0 ? " (latest)" : ""}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={() => setModal("delete")}
            disabled={!list.length}
            className={`${btn} text-red-700 hover:bg-red-50 disabled:opacity-40`}
          >
            <Trash2 size={14} /> Delete file
          </button>
        </div>
      </div>

      <WindowBar
        windowInfo={data?.window}
        value={window}
        onChange={(w) => setParams({ file: fileId, window: w })}
        onRefresh={() => {
          files.reload();
          dash.reload();
        }}
        loading={dash.loading}
      />

      {(files.error || dash.error) && (
        <ErrorState error={files.error || dash.error} onRetry={() => { files.reload(); dash.reload(); }} />
      )}
      {(files.loading || dash.loading) && !data && !files.error && !dash.error && <Loading text="Loading dashboard…" />}

      {s && (
        <>
          <section className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
            <SummaryCard label="Integrations" value={s.total_integrations} />
            <SummaryCard label="Healthy" value={s.healthy} tone="healthy" />
            <SummaryCard label="Degraded" value={s.degraded} tone="degraded" />
            <SummaryCard label="Critical" value={s.critical} tone="critical" />
            <SummaryCard label="Unknown" value={s.unknown} tone="unknown" hint="too few requests" />
            <SummaryCard label="Requests" value={s.total_requests} />
            <SummaryCard
              label="Failure rate"
              value={pct(s.overall_failure_rate)}
              hint={`${s.total_failures} of ${s.total_requests} failed`}
            />
          </section>

          <section className="space-y-3">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              Needs attention ({data.needs_attention.length})
            </h2>
            <NeedsAttention items={data.needs_attention} window={window} fileId={fileId} />
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <FailureRateChart items={data.integrations} thresholds={chartThresholds} />
            <OutcomeMixChart items={data.integrations} />
          </section>

          <section className="space-y-3">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">All integrations</h2>
            <IntegrationTable items={data.integrations} window={window} fileId={fileId} />
          </section>
        </>
      )}

      {modal === "upload" && <UploadModal onClose={() => setModal(null)} onUploaded={onUploaded} />}
      {modal === "delete" && (
        <DeleteModal files={list} currentId={fileId} onClose={() => setModal(null)} onDeleted={onDeleted} />
      )}
    </div>
  );
}
