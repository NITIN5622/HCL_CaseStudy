import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, ReferenceLine,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { utc } from "../services/format.js";

// Validated palette (dataviz validator: chroma, CVD, contrast all PASS).
export const OUTCOME_COLORS = { success: "#059669", error: "#dc2626", timeout: "#7c3aed" };
const HEALTH_COLORS = { critical: "#dc2626", degraded: "#d97706", healthy: "#059669", unknown: "#94a3b8" };
const AXIS = { fontSize: 12, fill: "#64748b" };
const GRID = "#e2e8f0";

function Card({ title, subtitle, children, height = 260 }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <p className="text-sm font-semibold text-slate-800">{title}</p>
      {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
      <div className="mt-3" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">{children}</ResponsiveContainer>
      </div>
    </div>
  );
}

function TooltipBox({ title, rows }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs shadow-md">
      <p className="mb-1 font-semibold text-slate-800">{title}</p>
      {rows.map(([label, value, color]) => (
        <p key={label} className="flex items-center gap-2 text-slate-600">
          {color && <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: color }} />}
          <span>{label}</span>
          <span className="ml-auto pl-3 font-medium tabular-nums text-slate-900">{value}</span>
        </p>
      ))}
    </div>
  );
}

const shortName = (n) => n.replace(/ (Notifications|Payroll Sync|Envelope API|Directory Sync|ATS Sync)$/, "");

// ---------------------------------------------------------- dashboard ----

export function FailureRateChart({ items, thresholds }) {
  const data = items.map((i) => ({
    name: shortName(i.name), full: i.name, health: i.health,
    rate: i.failure_rate ?? 0, hasData: i.failure_rate !== null,
  }));
  return (
    <Card title="Failure rate by integration" subtitle="(errors + timeouts) / requests · bar colour = health status">
      <BarChart data={data} layout="vertical" margin={{ top: 18, left: 8, right: 24 }} barCategoryGap={10}>
        <CartesianGrid horizontal={false} stroke={GRID} />
        <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={AXIS} axisLine={false} tickLine={false} />
        <YAxis type="category" dataKey="name" width={90} tick={AXIS} axisLine={false} tickLine={false} />
        {thresholds.map((t) => (
          <ReferenceLine key={t.value} x={t.value} stroke={t.color} strokeDasharray="4 4"
            label={{ value: t.label, position: "top", fontSize: 11, fill: t.color }} />
        ))}
        <Tooltip
          cursor={{ fill: "#f1f5f9" }}
          content={({ active, payload }) =>
            active && payload?.length ? (
              <TooltipBox title={payload[0].payload.full} rows={[
                ["Failure rate", payload[0].payload.hasData ? `${payload[0].payload.rate.toFixed(2)}%` : "no data"],
                ["Health", payload[0].payload.health],
              ]} />
            ) : null
          }
        />
        <Bar isAnimationActive={false} dataKey="rate" radius={[0, 4, 4, 0]} maxBarSize={22}>
          {data.map((d) => <Cell key={d.full} fill={HEALTH_COLORS[d.health]} />)}
        </Bar>
      </BarChart>
    </Card>
  );
}

export function OutcomeMixChart({ items }) {
  const data = items.map((i) => ({
    name: shortName(i.name), full: i.name,
    success: i.successes, error: i.errors, timeout: i.timeouts,
  }));
  return (
    <Card title="Request outcomes by integration" subtitle="Number of requests in the window">
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 24 }} barCategoryGap={10}>
        <CartesianGrid horizontal={false} stroke={GRID} />
        <XAxis type="number" allowDecimals={false} tick={AXIS} axisLine={false} tickLine={false} />
        <YAxis type="category" dataKey="name" width={90} tick={AXIS} axisLine={false} tickLine={false} />
        <Tooltip
          cursor={{ fill: "#f1f5f9" }}
          content={({ active, payload }) =>
            active && payload?.length ? (
              <TooltipBox title={payload[0].payload.full} rows={[
                ["Success", payload[0].payload.success, OUTCOME_COLORS.success],
                ["Error", payload[0].payload.error, OUTCOME_COLORS.error],
                ["Timeout", payload[0].payload.timeout, OUTCOME_COLORS.timeout],
              ]} />
            ) : null
          }
        />
        <Legend iconType="square" wrapperStyle={{ fontSize: 12 }} />
        {["success", "error", "timeout"].map((k, idx, arr) => (
          <Bar isAnimationActive={false} key={k} dataKey={k} name={k[0].toUpperCase() + k.slice(1)} stackId="a"
            fill={OUTCOME_COLORS[k]} stroke="#ffffff" strokeWidth={2} maxBarSize={22}
            radius={idx === arr.length - 1 ? [0, 4, 4, 0] : 0} />
        ))}
      </BarChart>
    </Card>
  );
}

// ------------------------------------------------------------ details ----

export function StatusTimelineChart({ trends }) {
  const data = trends.buckets.map((b) => ({ ...b, label: utc(b.start) }));
  return (
    <Card title="Requests over time" subtitle={`${trends.bucket_minutes}-minute buckets (UTC)`}>
      <BarChart data={data} margin={{ left: -16, right: 8 }} barCategoryGap={4}>
        <CartesianGrid vertical={false} stroke={GRID} />
        <XAxis dataKey="label" tick={AXIS} axisLine={false} tickLine={false} minTickGap={12} />
        <YAxis allowDecimals={false} tick={AXIS} axisLine={false} tickLine={false} />
        <Tooltip
          cursor={{ fill: "#f1f5f9" }}
          content={({ active, payload }) =>
            active && payload?.length ? (
              <TooltipBox title={`${payload[0].payload.label} UTC`} rows={[
                ["Success", payload[0].payload.success, OUTCOME_COLORS.success],
                ["Error", payload[0].payload.error, OUTCOME_COLORS.error],
                ["Timeout", payload[0].payload.timeout, OUTCOME_COLORS.timeout],
              ]} />
            ) : null
          }
        />
        <Legend iconType="square" wrapperStyle={{ fontSize: 12 }} />
        {["success", "error", "timeout"].map((k, idx, arr) => (
          <Bar isAnimationActive={false} key={k} dataKey={k} name={k[0].toUpperCase() + k.slice(1)} stackId="a"
            fill={OUTCOME_COLORS[k]} stroke="#ffffff" strokeWidth={2}
            radius={idx === arr.length - 1 ? [4, 4, 0, 0] : 0} />
        ))}
      </BarChart>
    </Card>
  );
}

export function LatencyChart({ trends, slo }) {
  const data = trends.buckets.map((b) => ({ label: utc(b.start), latency: b.avg_latency_ms }));
  const max = Math.max(slo * 1.15, ...data.map((d) => d.latency || 0));
  return (
    <Card title="Average success latency over time" subtitle="Successful requests only · dashed line = latency SLO">
      <LineChart data={data} margin={{ left: -4, right: 8 }}>
        <CartesianGrid vertical={false} stroke={GRID} />
        <XAxis dataKey="label" tick={AXIS} axisLine={false} tickLine={false} minTickGap={12} />
        <YAxis domain={[0, Math.ceil(max / 100) * 100]} tickFormatter={(v) => `${v}`} unit=" ms"
          tick={AXIS} axisLine={false} tickLine={false} width={64} />
        <ReferenceLine y={slo} stroke="#d97706" strokeDasharray="4 4"
          label={{ value: `SLO ${slo} ms`, position: "insideTopRight", fontSize: 11, fill: "#b45309" }} />
        <Tooltip
          content={({ active, payload }) =>
            active && payload?.length ? (
              <TooltipBox title={`${payload[0].payload.label} UTC`} rows={[
                ["Avg latency", payload[0].payload.latency == null ? "no successes" : `${Math.round(payload[0].payload.latency)} ms`, "#4f46e5"],
              ]} />
            ) : null
          }
        />
        <Line isAnimationActive={false} type="monotone" dataKey="latency" stroke="#4f46e5" strokeWidth={2} connectNulls={false}
          dot={{ r: 4, fill: "#4f46e5", stroke: "#fff", strokeWidth: 2 }} activeDot={{ r: 5 }} />
      </LineChart>
    </Card>
  );
}
