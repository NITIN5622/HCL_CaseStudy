export const pct = (v) => (v === null || v === undefined ? "—" : `${v.toFixed(2)}%`);

export const ms = (v) => (v === null || v === undefined ? "—" : `${Math.round(v).toLocaleString()} ms`);

// Backend timestamps are UTC; show them in UTC so they match the raw logs.
export const utc = (iso, withDate = false) => {
  if (!iso) return "—";
  const d = new Date(iso).toISOString();
  return withDate ? `${d.slice(0, 10)} ${d.slice(11, 16)} UTC` : d.slice(11, 16);
};

// Upload time in the viewer's local time, e.g. "27 Nov, 12:40".
export const localTime = (iso) =>
  new Date(iso).toLocaleString(undefined, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

export const fileLabel = (f) => `${f.filename} · ${f.log_count} logs · ${localTime(f.uploaded_at)}`;

export const WINDOWS = ["15m", "30m", "1h", "6h", "24h", "7d", "all"];
