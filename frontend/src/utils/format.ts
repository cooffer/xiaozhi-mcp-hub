import type { ServerFormState, ServerPayload } from "../types";

export function splitList(value: string): string[] {
  return String(value || "")
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export function parseEnv(value: string): Record<string, string> {
  return String(value || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .reduce<Record<string, string>>((acc, line) => {
      const index = line.indexOf("=");
      if (index > 0) acc[line.slice(0, index).trim()] = line.slice(index + 1).trim();
      return acc;
    }, {});
}

export function serverPayload(form: ServerFormState): ServerPayload {
  return {
    id: form.id.trim(),
    transport: form.transport,
    namespace: form.namespace.trim(),
    tenant_id: form.tenant_id.trim() || "default",
    endpoint: form.endpoint.trim() || null,
    command: form.command.trim() || null,
    args: splitList(form.argsText),
    env: parseEnv(form.envText),
    auth: {
      type: form.authType,
      token_ref: form.tokenRef || null,
      api_key_ref: form.apiKeyRef || null,
      header_name: form.headerName || null
    },
    enabled: form.enabled,
    timeout_ms: Number(form.timeout_ms) || 30000,
    tags: splitList(form.tagsText)
  };
}

export function maskEndpoint(value?: string | null): string {
  if (!value) return "-";
  return value.replace(/([?&][^=]+=)[^&]+/g, "$1***").replace(/(token|key|secret)=([^&]+)/gi, "$1=***");
}

export function formatDate(value?: string | null): string {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString();
}

