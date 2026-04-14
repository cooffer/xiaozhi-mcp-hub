import type { ServerFormState } from "./types";

export const blankUpstream = {
  id: "",
  channel: "xiaozhi_official",
  type: "xiaozhi_official",
  endpoint: "",
  enabled: true,
  envelope_mode: "raw"
};

export const blankServer: ServerFormState = {
  id: "",
  transport: "stdio",
  namespace: "",
  tenant_id: "default",
  endpoint: "",
  command: "",
  argsText: "",
  envText: "",
  authType: "none",
  tokenRef: "",
  apiKeyRef: "",
  headerName: "",
  enabled: true,
  timeout_ms: 30000,
  tagsText: ""
};

