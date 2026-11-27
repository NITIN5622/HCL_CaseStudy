import { useState } from "react";
import { Trash2, X } from "lucide-react";
import { api } from "../services/api.js";
import { fileLabel } from "../services/format.js";
import UploadBox from "./UploadBox.jsx";

function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-900/40 p-4" role="dialog" aria-modal="true">
      <div className="w-full max-w-lg rounded-2xl bg-white p-5 shadow-xl">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
          <button onClick={onClose} aria-label="Close" className="rounded-md p-1 text-slate-500 hover:bg-slate-100">
            <X size={18} />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function UploadModal({ onClose, onUploaded }) {
  return (
    <Modal title="Upload logs" onClose={onClose}>
      <UploadBox compact onUploaded={onUploaded} />
    </Modal>
  );
}

export function DeleteModal({ files, currentId, onClose, onDeleted }) {
  const [target, setTarget] = useState(currentId);
  const [token, setToken] = useState("");
  const [needsToken, setNeedsToken] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const file = files.find((f) => f.id === target);

  const remove = async () => {
    setBusy(true);
    setError(null);
    try {
      const result = await api.deleteFile(target, token.trim());
      onDeleted(target, result);
    } catch (err) {
      if (err.status === 401) setNeedsToken(true);
      setError(err.message);
      setBusy(false);
    }
  };

  return (
    <Modal title="Delete a log file" onClose={onClose}>
      <label className="text-sm font-medium text-slate-700" htmlFor="delete-file">File to delete</label>
      <select
        id="delete-file"
        value={target}
        onChange={(e) => setTarget(e.target.value)}
        className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
      >
        {files.map((f) => (
          <option key={f.id} value={f.id}>
            {fileLabel(f)}{f.id === currentId ? " (viewing)" : ""}
          </option>
        ))}
      </select>

      <p className="mt-3 rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
        <span className="font-medium">{file?.filename}</span> will be permanently removed. This cannot be undone.
        {target === currentId && files.length > 1 && " The dashboard will switch to the most recent remaining file."}
        {files.length === 1 && " This is the last file, so you will return to the upload page."}
      </p>

      {needsToken && (
        <input
          type="password"
          placeholder="Admin token"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          className="mt-3 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
      )}
      {error && <p className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-800">{error}</p>}

      <div className="mt-4 flex justify-end gap-2">
        <button onClick={onClose} className="rounded-lg px-4 py-2 text-sm ring-1 ring-slate-300 hover:bg-slate-50">
          Cancel
        </button>
        <button
          onClick={remove}
          disabled={!target || busy}
          className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
        >
          <Trash2 size={15} /> {busy ? "Deleting…" : "Delete file"}
        </button>
      </div>
    </Modal>
  );
}
