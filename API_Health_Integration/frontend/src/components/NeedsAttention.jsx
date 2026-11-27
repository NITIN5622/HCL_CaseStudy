import { ArrowRight, CheckCircle2 } from "lucide-react";
import { Link } from "react-router-dom";
import HealthBadge from "./HealthBadge.jsx";
import { pct } from "../services/format.js";

const BORDER = { critical: "border-l-red-500", degraded: "border-l-amber-500", unknown: "border-l-slate-400" };

export default function NeedsAttention({ items, window, fileId }) {
  if (!items.length) {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
        <CheckCircle2 size={16} /> All integrations are healthy in this window.
      </div>
    );
  }
  return (
    <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
      {items.map((i) => (
        <Link
          key={i.id}
          to={`/integrations/${i.id}?file=${fileId}&window=${window}`}
          className={`group rounded-xl border border-slate-200 border-l-4 ${BORDER[i.health]} bg-white p-4 hover:shadow-sm`}
        >
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="font-semibold text-slate-900">{i.name}</p>
              <p className="text-xs text-slate-500 capitalize">{i.tier} tier</p>
            </div>
            <HealthBadge health={i.health} />
          </div>
          <p className="mt-3 text-sm text-slate-700">
            <span className="font-semibold tabular-nums">{pct(i.failure_rate)}</span> failing
            {i.dominant_failure && (
              <> · mostly <span className="font-medium">{i.dominant_failure}</span></>
            )}
          </p>
          <ul className="mt-1 space-y-0.5 text-xs text-slate-500">
            {i.reasons.map((r) => <li key={r}>{r}</li>)}
          </ul>
          {i.next_step && (
            <p className="mt-3 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-700">
              <span className="font-semibold">Next step:</span> {i.next_step}
            </p>
          )}
          <span className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-indigo-600 group-hover:underline">
            View evidence <ArrowRight size={12} />
          </span>
        </Link>
      ))}
    </div>
  );
}
