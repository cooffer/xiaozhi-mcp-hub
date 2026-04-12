CREATE TABLE IF NOT EXISTS tenants (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL,
  tenant_id TEXT NOT NULL DEFAULT 'default',
  active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS upstreams (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  tenant_id TEXT NOT NULL DEFAULT 'default',
  enabled BOOLEAN NOT NULL DEFAULT true,
  envelope_mode TEXT NOT NULL DEFAULT 'raw',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS downstream_servers (
  id TEXT PRIMARY KEY,
  transport TEXT NOT NULL,
  namespace TEXT NOT NULL,
  tenant_id TEXT NOT NULL DEFAULT 'default',
  endpoint TEXT,
  command TEXT,
  args JSONB NOT NULL DEFAULT '[]',
  env JSONB NOT NULL DEFAULT '{}',
  auth JSONB NOT NULL DEFAULT '{}',
  enabled BOOLEAN NOT NULL DEFAULT true,
  timeout_ms INTEGER NOT NULL DEFAULT 30000,
  tags JSONB NOT NULL DEFAULT '[]',
  status TEXT NOT NULL DEFAULT 'unknown',
  latency_ms DOUBLE PRECISION,
  failure_count INTEGER NOT NULL DEFAULT 0,
  circuit_open_until TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tools (
  tool_id TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  server_id TEXT NOT NULL REFERENCES downstream_servers(id) ON DELETE CASCADE,
  origin_tool_name TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  input_schema JSONB NOT NULL DEFAULT '{}',
  annotations JSONB NOT NULL DEFAULT '{}',
  enabled BOOLEAN NOT NULL DEFAULT true,
  risk_level TEXT NOT NULL DEFAULT 'low',
  tenant_id TEXT NOT NULL DEFAULT 'default',
  device_scope JSONB NOT NULL DEFAULT '[]',
  tags JSONB NOT NULL DEFAULT '[]',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tool_acl (
  id TEXT PRIMARY KEY,
  tool_id TEXT NOT NULL REFERENCES tools(tool_id) ON DELETE CASCADE,
  tenant_id TEXT NOT NULL DEFAULT 'default',
  roles JSONB NOT NULL DEFAULT '["admin","operator"]',
  upstream_ids JSONB NOT NULL DEFAULT '[]',
  device_scope JSONB NOT NULL DEFAULT '[]',
  enabled BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS approvals (
  id TEXT PRIMARY KEY,
  tool_id TEXT NOT NULL,
  arguments JSONB NOT NULL DEFAULT '{}',
  status TEXT NOT NULL,
  tenant_id TEXT NOT NULL DEFAULT 'default',
  trace_id TEXT NOT NULL,
  requested_by TEXT,
  decided_by TEXT,
  reason TEXT,
  result JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  decided_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id TEXT PRIMARY KEY,
  trace_id TEXT NOT NULL,
  action TEXT NOT NULL,
  tenant_id TEXT NOT NULL DEFAULT 'default',
  actor_id TEXT,
  tool_id TEXT,
  server_id TEXT,
  status TEXT NOT NULL,
  latency_ms DOUBLE PRECISION,
  error TEXT,
  metadata JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS config_versions (
  id TEXT PRIMARY KEY,
  version INTEGER NOT NULL,
  payload JSONB NOT NULL,
  created_by TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
