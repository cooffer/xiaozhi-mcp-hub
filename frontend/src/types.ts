import type { Locale, Translator } from "./i18n";

export type { Locale, Translator };

export type ActivePage = "overview" | "upstreams" | "servers" | "tools" | "config" | "approvals" | "audit";
export type TransportType = "stdio" | "streamable_http" | "sse";

export interface User {
  id: string;
  email: string;
  role: "admin" | "operator" | "viewer" | string;
  tenant_id: string;
}

export interface Summary {
  servers?: number;
  tools?: number;
  healthy_servers?: number;
  pending_approvals?: number;
}

export interface Upstream {
  id: string;
  channel?: string;
  type?: string;
  endpoint: string;
  enabled: boolean;
}

export interface DownstreamServer {
  id: string;
  transport: TransportType | string;
  namespace: string;
  tenant_id?: string;
  endpoint?: string | null;
  command?: string | null;
  enabled: boolean;
  status?: string;
  latency_ms?: number | null;
}

export interface ToolRecord {
  tool_id: string;
  display_name: string;
  server_id: string;
  origin_tool_name: string;
  description?: string;
  enabled: boolean;
  risk_level?: string;
}

export interface Approval {
  id: string;
  tool_id: string;
  status: string;
  created_at?: string;
}

export interface AuditLog {
  id: string;
  action: string;
  status: string;
  tool_id?: string | null;
  trace_id: string;
  error?: string | null;
}

export interface DashboardData {
  summary: Summary;
  upstreams: Upstream[];
  servers: DownstreamServer[];
  tools: ToolRecord[];
  approvals: Approval[];
  audit: AuditLog[];
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user?: User;
}

export interface BootstrapStatus {
  registration_open: boolean;
}

export interface ImportResult {
  upstreams: number;
  servers: number;
  tools?: number;
  errors?: Record<string, string>;
  version: number;
}

export interface ConfigImportInput {
  raw: string;
  file: File | null;
}

export interface UpstreamPayload {
  id: string | null;
  channel: string;
  type: string;
  endpoint: string;
  enabled: boolean;
}

export interface ServerFormState {
  id: string;
  transport: TransportType;
  namespace: string;
  tenant_id: string;
  endpoint: string;
  command: string;
  argsText: string;
  envText: string;
  authType: "none" | "bearer" | "api_key";
  tokenRef: string;
  apiKeyRef: string;
  headerName: string;
  enabled: boolean;
  timeout_ms: number;
  tagsText: string;
}

export interface ServerPayload {
  id: string;
  transport: TransportType;
  namespace: string;
  tenant_id: string;
  endpoint: string | null;
  command: string | null;
  args: string[];
  env: Record<string, string>;
  auth: {
    type: string;
    token_ref: string | null;
    api_key_ref: string | null;
    header_name: string | null;
  };
  enabled: boolean;
  timeout_ms: number;
  tags: string[];
}

