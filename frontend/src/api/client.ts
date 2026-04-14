import type {
  Approval,
  AuditLog,
  BootstrapStatus,
  ConfigImportInput,
  DownstreamServer,
  ImportResult,
  LoginResponse,
  ServerPayload,
  Summary,
  ToolRecord,
  Upstream,
  UpstreamPayload,
  User
} from "../types";

const API_BASE = "/api/v1";

export class ApiRequestError extends Error {
  status?: number;
  path?: string;
}

export function createApiClient(token = "") {
  async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers = new Headers(options.headers);
    if (!(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
    if (token) headers.set("Authorization", `Bearer ${token}`);

    const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
    if (!response.ok) {
      const error = new ApiRequestError(await response.text());
      error.status = response.status;
      error.path = path;
      throw error;
    }
    return response.status === 204 ? (null as T) : response.json();
  }

  return {
    bootstrapStatus: () => request<BootstrapStatus>("/auth/bootstrap-status"),
    login: (email: string, password: string) => request<LoginResponse>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
    register: (email: string, password: string) => request<LoginResponse>("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) }),
    me: () => request<User>("/auth/me"),
    summary: () => request<Summary>("/dashboard/summary"),
    upstreams: () => request<Upstream[]>("/upstreams"),
    saveUpstream: (payload: UpstreamPayload) => request<Upstream>("/upstreams", { method: "POST", body: JSON.stringify(payload) }),
    servers: () => request<DownstreamServer[]>("/servers"),
    saveServer: (payload: ServerPayload) => request<DownstreamServer>("/servers", { method: "POST", body: JSON.stringify(payload) }),
    tools: () => request<ToolRecord[]>("/tools"),
    approvals: () => request<Approval[]>("/approvals"),
    audit: () => request<AuditLog[]>("/audit-logs?limit=50"),
    approve: (id: string) => request<Approval>(`/approvals/${id}/approve`, { method: "POST" }),
    reject: (id: string, reason: string) => request<Approval>(`/approvals/${id}/reject`, { method: "POST", body: JSON.stringify({ reason }) }),
    discover: (id: string) => request<{ server_id: string; tools: number }>(`/servers/${id}/discover`, { method: "POST" }),
    importConfig: ({ raw, file }: ConfigImportInput) => {
      const form = new FormData();
      if (file) form.append("file", file);
      if (raw.trim()) form.append("raw", raw);
      return request<ImportResult>("/config/import", { method: "POST", body: form });
    }
  };
}

export type ApiClient = ReturnType<typeof createApiClient>;

