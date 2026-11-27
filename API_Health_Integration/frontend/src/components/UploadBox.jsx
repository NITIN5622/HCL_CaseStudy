import { useRef, useState } from "react";
import { FileJson, Upload } from "lucide-react";
import { api } from "../services/api.js";

// Pick a JSON file and upload it. Shows the import summary or the error.
export default function UploadBox({ onUploaded, compact = false }) {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [token, setToken] = useState("");
  const [needsToken, setNeedsToken] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(null); // {kind: "ok"|"error", text, summary?}

  const submit = async () => {
    if (!file) return;
    setBusy(true);
    setMessage(null);
    try {
      const { file: info, summary } = await api.uploadFile(file, token.trim());
      setMessage({
        kind: "ok",
        text: `Uploaded "${info.filename}"`,
        summary,
      });
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
      onUploaded(info);
    } catch (err) {
      if (err.status === 401) setNeedsToken(true);
      setMessage({ kind: "error", text: err.message, summary: err.body?.summary });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-3">
      <label
        className={`flex cursor-pointer items-center gap-3 rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 hover:border-indigo-400 hover:bg-indigo-50/40 ${
          compact ? "p-3" : "p-6"
        }`}
      >
        <FileJson className="shrink-0 text-indigo-500" size={compact ? 22 : 28} />
        <span className="min-w-0 text-sm">
          <span className="block truncate font-medium text-slate-800">
            {file ? file.name : "Choose a JSON log file"}
          </span>
          <span className="block text-xs text-slate-500">
            {file ? `${(file.size / 1024).toFixed(1)} KB` : 'Format: {"logs": [ ... ]}'}
          </span>
        </span>
        <input
          ref={inputRef}
          type="file"
          accept="application/json,.json"
          className="sr-only"
          onChange={(e) => {
            setFile(e.target.files?.[0] || null);
            setMessage(null);
          }}
        />
      </label>

      {needsToken && (
        <input
          type="password"
          placeholder="Admin token"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
      )}

      <button
        onClick={submit}
        disabled={!file || busy}
        className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        <Upload size={15} /> {busy ? "Uploading…" : "Upload logs"}
      </button>

      {message && (
        <div
          className={`rounded-lg p-3 text-sm ${
            message.kind === "ok" ? "bg-emerald-50 text-emerald-800" : "bg-red-50 text-red-800"
          }`}
        >
          <p className="font-medium">{message.text}</p>
          {message.summary && (
            <p className="mt-1 text-xs">
              Received {message.summary.received} · imported {message.summary.imported} · invalid{" "}
              {message.summary.invalid} · duplicate rows {message.summary.duplicates}
            </p>
          )}
          {message.summary?.errors?.length > 0 && (
            <ul className="mt-2 max-h-28 space-y-0.5 overflow-y-auto text-xs">
              {message.summary.errors.slice(0, 20).map((e) => (
                <li key={e.index}>Row {e.index}: {e.error}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
