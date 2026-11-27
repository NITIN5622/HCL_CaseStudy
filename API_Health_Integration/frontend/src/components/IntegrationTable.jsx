import { useNavigate } from "react-router-dom";
import HealthBadge from "./HealthBadge.jsx";
import { ms, pct } from "../services/format.js";

export default function IntegrationTable({ items, window, fileId }) {
  const navigate = useNavigate();
  const open = (id) => navigate(`/integrations/${id}?file=${fileId}&window=${window}`);

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3 font-medium">Integration</th>
            <th className="px-4 py-3 font-medium">Health</th>
            <th className="px-4 py-3 text-right font-medium">Requests</th>
            <th className="px-4 py-3 text-right font-medium">Failure rate</th>
            <th className="px-4 py-3 text-right font-medium">Timeout rate</th>
            <th className="px-4 py-3 text-right font-medium">Avg latency</th>
            <th className="px-4 py-3 font-medium">Dominant failure</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {items.map((i) => (
            <tr
              key={i.id}
              onClick={() => open(i.id)}
              onKeyDown={(e) => e.key === "Enter" && open(i.id)}
              tabIndex={0}
              className="cursor-pointer hover:bg-slate-50 focus:bg-slate-50 focus:outline-none"
            >
              <td className="px-4 py-3">
                <p className="font-medium text-slate-900">{i.name}</p>
                <p className="text-xs capitalize text-slate-500">{i.tier} tier</p>
              </td>
              <td className="px-4 py-3"><HealthBadge health={i.health} /></td>
              <td className="px-4 py-3 text-right tabular-nums">{i.total_requests}</td>
              <td className="px-4 py-3 text-right tabular-nums">{pct(i.failure_rate)}</td>
              <td className="px-4 py-3 text-right tabular-nums">{pct(i.timeout_rate)}</td>
              <td className="px-4 py-3 text-right tabular-nums">{ms(i.avg_latency_ms)}</td>
              <td className="px-4 py-3 text-slate-600">{i.dominant_failure || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
