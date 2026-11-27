import { AlertCircle, Loader2 } from "lucide-react";

export function Loading({ text = "Loading…" }) {
  return (
    <div className="flex items-center gap-2 py-16 justify-center text-slate-500">
      <Loader2 size={18} className="animate-spin" /> {text}
    </div>
  );
}

export function ErrorState({ error, onRetry }) {
  return (
    <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
      <div className="flex items-center gap-2 font-medium">
        <AlertCircle size={16} /> Something went wrong
      </div>
      <p className="mt-1">{error?.message || String(error)}</p>
      {onRetry && (
        <button onClick={onRetry} className="mt-3 rounded-lg bg-white px-3 py-1.5 font-medium ring-1 ring-red-200 hover:bg-red-100">
          Retry
        </button>
      )}
    </div>
  );
}

export function Empty({ children }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
      {children}
    </div>
  );
}
