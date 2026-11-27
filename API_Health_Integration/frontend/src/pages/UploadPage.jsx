import { useState } from "react";
import { ArrowRight, Files } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { ErrorState, Loading } from "../components/States.jsx";
import UploadBox from "../components/UploadBox.jsx";
import { api } from "../services/api.js";
import { fileLabel } from "../services/format.js";
import { useApi } from "../services/useApi.js";

// First page: upload log files, see existing ones, continue once >= 1 file exists.
export default function UploadPage() {
  const navigate = useNavigate();
  const files = useApi(() => api.listFiles(), []);
  const [selected, setSelected] = useState("");

  const list = files.data || [];
  const count = list.length;

  return (
    <div className="mx-auto max-w-xl space-y-6 pt-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Upload integration logs</h1>
        <p className="mt-1 text-sm text-slate-500">
          Upload one or more request-log files. The dashboard analyses one file at a time.
        </p>
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <UploadBox
          onUploaded={(info) => {
            files.reload();
            setSelected(info.id);
          }}
        />
      </section>

      <section className="space-y-3 rounded-2xl border border-slate-200 bg-white p-5">
        <div className="flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-800">
            <Files size={16} /> Existing log files
          </h2>
          <span
            className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
              count ? "bg-indigo-50 text-indigo-700" : "bg-slate-100 text-slate-500"
            }`}
          >
            {count} file{count === 1 ? "" : "s"}
          </span>
        </div>

        {files.error && <ErrorState error={files.error} onRetry={files.reload} />}
        {files.loading && !files.data && <Loading text="Loading files…" />}
        {files.data && (
          <select
            value={selected || list[0]?.id || ""}
            onChange={(e) => setSelected(e.target.value)}
            disabled={!count}
            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm disabled:bg-slate-50 disabled:text-slate-400"
          >
            {!count && <option value="">No files uploaded yet</option>}
            {list.map((f) => (
              <option key={f.id} value={f.id}>{fileLabel(f)}</option>
            ))}
          </select>
        )}

        <button
          onClick={() => navigate("/dashboard")}
          disabled={count < 1}
          className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Continue to dashboard <ArrowRight size={15} />
        </button>
        {count < 1 && (
          <p className="text-center text-xs text-slate-500">Upload at least one file to continue.</p>
        )}
        {count >= 1 && (
          <p className="text-center text-xs text-slate-500">The dashboard opens on the most recent file.</p>
        )}
      </section>
    </div>
  );
}
