// Thin API client. All health logic lives in the backend; this only fetches.
const BASE = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(message, status, body) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(`${BASE}${path}`, options);
  } catch {
    throw new ApiError(`Cannot reach the backend at ${BASE}. Is it running?`, 0, null);
  }
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    let detail = body?.detail;
    if (Array.isArray(detail)) detail = detail.map((d) => d.msg).join("; ");
    throw new ApiError(detail || `Request failed (${res.status})`, res.status, body);
  }
  return body;
}

const qs = (params) =>
  new URLSearchParams(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "")
  ).toString();

const adminHeaders = (token) => (token ? { "X-Admin-Token": token } : {});

export const api = {
  // files
  listFiles: () => request("/api/files"),
  uploadFile: (file, token) => {
    const form = new FormData();
    form.append("file", file);
    return request("/api/files", { method: "POST", body: form, headers: adminHeaders(token) });
  },
  deleteFile: (fileId, token) =>
    request(`/api/files/${encodeURIComponent(fileId)}`, { method: "DELETE", headers: adminHeaders(token) }),

  thresholds: () => request("/api/config/thresholds"),

  // analysis (always for one file)
  dashboard: (fileId, window) => request(`/api/dashboard?${qs({ file_id: fileId, window })}`),
  integration: (fileId, id, window) =>
    request(`/api/integrations/${encodeURIComponent(id)}?${qs({ file_id: fileId, window })}`),
  integrationLogs: (fileId, id, { window, status, page, pageSize }) =>
    request(
      `/api/integrations/${encodeURIComponent(id)}/logs?${qs({
        file_id: fileId, window, status, page, page_size: pageSize,
      })}`
    ),
  integrationTrends: (fileId, id, window) =>
    request(`/api/integrations/${encodeURIComponent(id)}/trends?${qs({ file_id: fileId, window })}`),
};
