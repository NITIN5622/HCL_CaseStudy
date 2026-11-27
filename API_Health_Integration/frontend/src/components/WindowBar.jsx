import { Clock, RefreshCw } from "lucide-react";
import { WINDOWS, utc } from "../services/format.js";

// Shows mode + covered time range, with window selector and refresh.
export default function WindowBar({ windowInfo, value, onChange, onRefresh, loading, children }) {
  const historical = windowInfo?.mode === "historical";
  return (
    <div className="flex flex-wrap items-center gap-3">
      {windowInfo && (
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
            historical ? "bg-indigo-50 text-indigo-700" : "bg-emerald-50 text-emerald-700"
          }`}
        >
          <Clock size={13} />
          {historical ? "Historical Demo Mode" : "Live"}
        </span>
      )}
      {windowInfo?.end && (
        <span className="text-xs text-slate-500">
          {windowInfo.start ? `${utc(windowInfo.start, true)} → ` : "All data up to "}
          {utc(windowInfo.end, true)}
        </span>
      )}
      <div className="ml-auto flex items-center gap-2">
        {children}
        <label className="sr-only" htmlFor="window">Time window</label>
        <select
          id="window"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-sm"
        >
          {WINDOWS.map((w) => (
            <option key={w} value={w}>
              Last {w === "all" ? "all data" : w}
            </option>
          ))}
        </select>
        <button
          onClick={onRefresh}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-50"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>
    </div>
  );
}
