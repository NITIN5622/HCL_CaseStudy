const TONES = {
  default: "text-slate-900",
  critical: "text-red-600",
  degraded: "text-amber-600",
  healthy: "text-emerald-600",
  unknown: "text-slate-500",
};

export default function SummaryCard({ label, value, hint, tone = "default" }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`mt-1 text-2xl font-semibold tabular-nums ${TONES[tone]}`}>{value}</p>
      {hint && <p className="mt-0.5 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}
