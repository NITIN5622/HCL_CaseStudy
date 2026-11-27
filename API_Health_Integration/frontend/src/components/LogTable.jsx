import { ms, utc } from "../services/format.js";

const STATUS_CLS = {
  success: "text-emerald-700 bg-emerald-50",
  error: "text-red-700 bg-red-50",
  timeout: "text-violet-700 bg-violet-50",
};

export default function LogTable({ page, onPage }) {
  const { items, total, page: current, page_size } = page;
  const pages = Math.max(1, Math.ceil(total / page_size));

  return (
    <div className="rounded-xl border border-slate-200 bg-white">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-2.5 font-medium">Time (UTC)</th>
              <th className="px-4 py-2.5 font-medium">Status</th>
              <th className="px-4 py-2.5 font-medium">HTTP code</th>
              <th className="px-4 py-2.5 text-right font-medium">Latency</th>
              <th className="px-4 py-2.5 font-medium">Source</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-6 text-center text-slate-500">No logs match.</td></tr>
            )}
            {items.map((l, idx) => (
              <tr key={`${l.timestamp}-${idx}`}>
                <td className="px-4 py-2 tabular-nums">{utc(l.timestamp, true)}</td>
                <td className="px-4 py-2">
                  <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${STATUS_CLS[l.status]}`}>{l.status}</span>
                </td>
                <td className="px-4 py-2 tabular-nums">{l.status_code ?? "—"}</td>
                <td className="px-4 py-2 text-right tabular-nums">{ms(l.latency_ms)}</td>
                <td className="px-4 py-2 text-xs text-slate-500">{l.source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between border-t border-slate-100 px-4 py-2.5 text-xs text-slate-500">
        <span>{total} log{total === 1 ? "" : "s"}</span>
        <div className="flex items-center gap-2">
          <button
            disabled={current <= 1}
            onClick={() => onPage(current - 1)}
            className="rounded-md px-2 py-1 ring-1 ring-slate-200 disabled:opacity-40 hover:bg-slate-50"
          >
            Prev
          </button>
          <span className="tabular-nums">Page {current} of {pages}</span>
          <button
            disabled={current >= pages}
            onClick={() => onPage(current + 1)}
            className="rounded-md px-2 py-1 ring-1 ring-slate-200 disabled:opacity-40 hover:bg-slate-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
