import { AlertOctagon, AlertTriangle, CheckCircle2, HelpCircle } from "lucide-react";

export const HEALTH_STYLES = {
  critical: { label: "Critical", cls: "bg-red-50 text-red-700 ring-red-200", Icon: AlertOctagon },
  degraded: { label: "Degraded", cls: "bg-amber-50 text-amber-800 ring-amber-200", Icon: AlertTriangle },
  healthy: { label: "Healthy", cls: "bg-emerald-50 text-emerald-700 ring-emerald-200", Icon: CheckCircle2 },
  unknown: { label: "Unknown", cls: "bg-slate-100 text-slate-600 ring-slate-200", Icon: HelpCircle },
};

export default function HealthBadge({ health, size = "sm" }) {
  const s = HEALTH_STYLES[health] || HEALTH_STYLES.unknown;
  const big = size === "lg";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium ring-1 ring-inset ${s.cls} ${
        big ? "px-3 py-1 text-sm" : "px-2 py-0.5 text-xs"
      }`}
    >
      <s.Icon size={big ? 16 : 13} />
      {s.label}
    </span>
  );
}
