import React, { useEffect, useMemo, useState } from "react";
import { LOCALES, createTranslator, detectLocale } from "./i18n_runtime.js";
import markImage from "../../logo.png";

const API_BASE = "/api/v1";
const MARK_IMAGE = markImage;

const ICONS = {
  overview: "M4 13.5 12 5l8 8.5M6 12.5V20h12v-7.5M9 20v-6h6v6",
  upstreams: "M12 4v16M5 8h6M5 16h6M13 8h6M13 16h6M5 8l-2 2 2 2M19 16l2-2-2-2",
  servers: "M5 6.5h14M5 12h14M5 17.5h14M7 4h10a2 2 0 0 1 2 2v1a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Zm0 6h10a2 2 0 0 1 2 2v1a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-1a2 2 0 0 1 2-2Zm0 6h10a2 2 0 0 1 2 2v1a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-1a2 2 0 0 1 2-2Z",
  tools: "M14.5 5.5 18 2l4 4-3.5 3.5M14.5 5.5l4 4M14.5 5.5 4 16v4h4L18.5 9.5",
  config: "M5 5h14v4H5zM5 15h14v4H5zM8 9v6M16 9v6",
  approvals: "M12 3 20 7v5c0 5-3.4 8.5-8 9-4.6-.5-8-4-8-9V7l8-4Zm-3 9 2 2 4-5",
  audit: "M7 4h10v16H7zM9.5 8h5M9.5 12h5M9.5 16h3",
  refresh: "M20 12a8 8 0 0 1-14.5 4.7M4 12A8 8 0 0 1 18.5 7.3M18.5 3v4h-4M5.5 21v-4h4",
  logout: "M10 6H6v12h4M13 8l4 4-4 4M8 12h9",
  language: "M4 5h9M8.5 3v2M6 5c.8 3.2 2.7 5.6 6 7M12 5c-.8 3.1-2.8 5.7-6.5 7.5M14 21l4-9 4 9M15.3 18h5.4",
  copy: "M8 8h10v12H8zM6 16H4V4h12v2",
  route: "M5 7a3 3 0 1 0 0 .1M19 17a3 3 0 1 0 0 .1M8 7h5a4 4 0 0 1 4 4v3",
  activity: "M4 12h4l2-6 4 12 2-6h4",
  check: "M5 12l4 4L19 6",
  x: "M6 6l12 12M18 6 6 18",
  add: "M12 5v14M5 12h14",
  save: "M5 5h12l2 2v12H5zM8 5v6h8M8 19v-5h8",
  upload: "M12 17V5M7 10l5-5 5 5M5 19h14"
};

const blankUpstream = {
  id: "",
  channel: "xiaozhi_official",
  type: "xiaozhi_official",
  endpoint: "",
  enabled: true,
  envelope_mode: "raw"
};

const blankServer = {
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

function Icon({ name, className = "" }) {
  return (
    <svg className={`icon ${className}`} viewBox="0 0 24 24" aria-hidden="true">
      <path d={ICONS[name]} />
    </svg>
  );
}

function api(token) {
  async function request(path, options = {}) {
    const headers = { ...(options.headers || {}) };
    if (!(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
    if (token) headers.Authorization = `Bearer ${token}`;
    const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
    if (!response.ok) {
      const error = new Error(await response.text());
      error.status = response.status;
      error.path = path;
      throw error;
    }
    return response.status === 204 ? null : response.json();
  }
  return {
    bootstrapStatus: () => request("/auth/bootstrap-status"),
    login: (email, password) => request("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
    register: (email, password) => request("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) }),
    me: () => request("/auth/me"),
    summary: () => request("/dashboard/summary"),
    upstreams: () => request("/upstreams"),
    saveUpstream: (payload) => request("/upstreams", { method: "POST", body: JSON.stringify(payload) }),
    servers: () => request("/servers"),
    saveServer: (payload) => request("/servers", { method: "POST", body: JSON.stringify(payload) }),
    tools: () => request("/tools"),
    approvals: () => request("/approvals"),
    audit: () => request("/audit-logs?limit=50"),
    approve: (id) => request(`/approvals/${id}/approve`, { method: "POST" }),
    reject: (id, reason) => request(`/approvals/${id}/reject`, { method: "POST", body: JSON.stringify({ reason }) }),
    discover: (id) => request(`/servers/${id}/discover`, { method: "POST" }),
    importConfig: ({ raw, file }) => {
      const form = new FormData();
      if (file) form.append("file", file);
      if (raw?.trim()) form.append("raw", raw);
      return request("/config/import", { method: "POST", body: form });
    }
  };
}

function LanguageSelect({ locale, onLocaleChange, t }) {
  return (
    <label className="language-select">
      <span><Icon name="language" />{t("language")}</span>
      <select value={locale} onChange={(event) => onLocaleChange(event.target.value)}>
        {LOCALES.map((item) => (
          <option key={item} value={item}>
            {item === "zh-CN" ? "中文" : "English"}
          </option>
        ))}
      </select>
    </label>
  );
}

function Login({ locale, onLocaleChange, onLogin, t }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [bootstrap, setBootstrap] = useState({ registration_open: false });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let alive = true;
    api()
      .bootstrapStatus()
      .then((result) => {
        if (!alive) return;
        setBootstrap(result);
        if (result.registration_open) setMode("register");
      })
      .catch(() => setBootstrap({ registration_open: false }));
    return () => {
      alive = false;
    };
  }, []);

  async function submitLogin(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const result = await api().login(email, password);
      onLogin(result.access_token);
    } catch (err) {
      setError(t("login.error"));
    } finally {
      setSubmitting(false);
    }
  }

  async function submitRegister(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const result = await api().register(registerEmail, registerPassword);
      onLogin(result.access_token);
    } catch (err) {
      setError(t("login.registerError"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-shell">
      <section className="login-panel login-brand">
        <div className="login-topline">
          <img src={MARK_IMAGE} alt="" className="brand-mark" />
          <LanguageSelect locale={locale} onLocaleChange={onLocaleChange} t={t} />
        </div>
        <p className="eyebrow">{t("login.eyebrow")}</p>
        <h1>{t("login.title")}</h1>
        <p className="hero-text">{t("login.subtitle")}</p>
        <div className="feature-strip">
          <span><Icon name="tools" />{t("login.point1")}</span>
          <span><Icon name="approvals" />{t("login.point2")}</span>
          <span><Icon name="audit" />{t("login.point3")}</span>
        </div>
        <div className="product-preview">
          <div className="preview-header">
            <strong>{t("login.previewTitle")}</strong>
            <Badge value="healthy" kind="status" prefix="status" t={t} />
          </div>
          <div className="preview-flow">
            <span>{t("login.previewStep1")}</span>
            <i />
            <span>{t("login.previewStep2")}</span>
            <i />
            <span>{t("login.previewStep3")}</span>
          </div>
          <div className="preview-metrics">
            <div><strong>128</strong><span>{t("login.previewMetric1")}</span></div>
            <div><strong>100%</strong><span>{t("login.previewMetric2")}</span></div>
          </div>
        </div>
      </section>
      <section className="login-panel auth-panel">
        <div className="auth-tabs">
          <button className={mode === "login" ? "tab active" : "tab"} onClick={() => setMode("login")}>{t("login.signInTab")}</button>
          {bootstrap.registration_open && (
            <button className={mode === "register" ? "tab active" : "tab"} onClick={() => setMode("register")}>{t("login.registerTab")}</button>
          )}
        </div>
        {mode === "register" && bootstrap.registration_open ? (
          <form className="login-form" onSubmit={submitRegister}>
            <div>
              <h2>{t("login.registerTitle")}</h2>
              <p>{t("login.registerHint")}</p>
            </div>
            <TextField label={t("login.email")} value={registerEmail} onChange={setRegisterEmail} autoComplete="email" />
            <TextField label={t("login.password")} type="password" value={registerPassword} onChange={setRegisterPassword} autoComplete="new-password" />
            {error && <div className="notice error">{error}</div>}
            <button className="button-content" disabled={submitting || !registerEmail || registerPassword.length < 8}>
              <span>{submitting ? t("loading") : t("login.registerSubmit")}</span>
              <Icon name="check" />
            </button>
          </form>
        ) : (
          <form className="login-form" onSubmit={submitLogin}>
            <div>
              <h2>{t("product")}</h2>
              <p>{t("login.hint")}</p>
            </div>
            <TextField label={t("login.email")} value={email} onChange={setEmail} autoComplete="email" />
            <TextField label={t("login.password")} type="password" value={password} onChange={setPassword} autoComplete="current-password" />
            {error && <div className="notice error">{error}</div>}
            <button className="button-content" disabled={submitting}>
              <span>{submitting ? t("loading") : t("login.submit")}</span>
              <Icon name="check" />
            </button>
          </form>
        )}
      </section>
    </main>
  );
}

function TextField({ label, value, onChange, type = "text", ...props }) {
  return (
    <label>
      {label}
      <input type={type} value={value} onChange={(event) => onChange(event.target.value)} {...props} />
    </label>
  );
}

function TextareaField({ label, value, onChange, rows = 4, ...props }) {
  return (
    <label>
      {label}
      <textarea rows={rows} value={value} onChange={(event) => onChange(event.target.value)} {...props} />
    </label>
  );
}

function ToggleField({ label, checked, onChange }) {
  return (
    <label className="toggle-field">
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
      <span>{label}</span>
    </label>
  );
}

function Badge({ value, kind = "neutral", t, prefix }) {
  const label = prefix ? t(`${prefix}.${value}`) : value;
  return <span className={`badge badge-${kind} badge-${String(value).replaceAll("_", "-")}`}>{label || value}</span>;
}

function Stat({ label, value, detail }) {
  return (
    <article className="stat">
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
      <svg className="sparkline" viewBox="0 0 120 36" aria-hidden="true">
        <path d="M4 27 C18 16 28 20 40 13 S62 9 76 18 96 31 116 10" />
      </svg>
      {detail && <small>{detail}</small>}
    </article>
  );
}

function EmptyState({ children }) {
  return <div className="empty-state">{children}</div>;
}

function Shell({ locale, onLocaleChange, user, active, setActive, onRefresh, onSignOut, loading, t, children }) {
  const navItems = ["overview", "upstreams", "servers", "tools", "config", "approvals", "audit"];
  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand-row">
          <img src={MARK_IMAGE} alt="" className="nav-mark" />
          <div>
            <strong>{t("product")}</strong>
            <span>{t("header.signedIn")}</span>
          </div>
        </div>
        <div className="account-card">
          <strong>{user?.email || t("loading")}</strong>
          <span>{t("header.tenant")}: {user?.tenant_id || "default"}</span>
          <span>{t("header.role")}: {user?.role || t("unknown")}</span>
        </div>
        <nav className="nav-list">
          {navItems.map((item) => (
            <button key={item} className={active === item ? "nav-item active" : "nav-item"} onClick={() => setActive(item)}>
              <Icon name={item} />
              <span>{t(`nav.${item}`)}</span>
            </button>
          ))}
        </nav>
      </aside>
      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">{t("header.title")}</p>
            <h1>{t(`sections.${active}`)}</h1>
            <p>{t("header.subtitle")}</p>
          </div>
          <div className="topbar-actions">
            <LanguageSelect locale={locale} onLocaleChange={onLocaleChange} t={t} />
            <button className="secondary button-content" onClick={onRefresh} disabled={loading}>
              <Icon name="refresh" />
              <span>{loading ? t("refreshing") : t("refresh")}</span>
            </button>
            <button className="ghost button-content" onClick={onSignOut}>
              <Icon name="logout" />
              <span>{t("signOut")}</span>
            </button>
          </div>
        </header>
        {children}
      </section>
    </main>
  );
}

function Overview({ data, t }) {
  return (
    <section className="overview-layout">
      <div className="dashboard-grid">
        <Stat label={t("stats.upstreams")} value={data.upstreams?.length ?? 0} detail={t("sections.upstreams")} />
        <Stat label={t("stats.tools")} value={data.summary.tools ?? 0} detail={t("sections.tools")} />
        <Stat label={t("stats.healthy")} value={data.summary.healthy_servers ?? 0} detail={t("status.healthy")} />
        <Stat label={t("stats.pending")} value={data.summary.pending_approvals ?? 0} detail={t("sections.approvals")} />
      </div>
      <div className="insight-grid">
        <article className="insight-card system-map">
          <div className="section-title">
            <Icon name="route" />
            <strong>{t("sections.systemMap")}</strong>
          </div>
          <div className="map-flow">
            <span>{t("overview.upstream")}</span>
            <i />
            <span>{t("overview.hub")}</span>
            <i />
            <span>{t("overview.policy")}</span>
            <i />
            <span>{t("overview.downstream")}</span>
          </div>
        </article>
        <article className="insight-card risk-mix">
          <div className="section-title">
            <Icon name="activity" />
            <strong>{t("sections.recentRisk")}</strong>
          </div>
          <div className="donut" style={{ "--high": `${Math.min(75, (data.summary.pending_approvals || 0) * 12)}deg` }} />
          <div className="risk-legend">
            <span><b className="dot low" />{t("risk.low")}</span>
            <span><b className="dot medium" />{t("risk.medium")}</span>
            <span><b className="dot high" />{t("risk.high")}</span>
          </div>
        </article>
      </div>
      {!data.servers.length && !data.tools.length && <EmptyState>{t("empty.overview")}</EmptyState>}
    </section>
  );
}

function Upstreams({ upstreams, onSave, actionId, t }) {
  const [form, setForm] = useState(blankUpstream);
  const [editingEndpoint, setEditingEndpoint] = useState("");
  const isEditing = Boolean(editingEndpoint);

  function setField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function edit(upstream) {
    setEditingEndpoint(upstream.endpoint);
    setForm({ ...blankUpstream, id: upstream.id, channel: upstream.channel || upstream.type || "xiaozhi_official", type: upstream.channel || upstream.type || "xiaozhi_official", endpoint: "", enabled: upstream.enabled });
  }

  function reset() {
    setEditingEndpoint("");
    setForm(blankUpstream);
  }

  function submit(event) {
    event.preventDefault();
    const endpoint = form.endpoint.trim() || editingEndpoint;
    onSave({ id: form.id || null, channel: form.channel, type: form.channel, endpoint, enabled: form.enabled });
    reset();
  }

  return (
    <section className="section-stack">
      <form className="form-panel" onSubmit={submit}>
        <div className="form-title">
          <Icon name="upstreams" />
          <div>
            <strong>{isEditing ? t("forms.editXiaozhi") : t("forms.addXiaozhi")}</strong>
            <span>{t("forms.upstreamHint")}</span>
          </div>
        </div>
        <div className="form-grid compact-form-grid">
          <label>
            {t("forms.channel")}
            <select value={form.channel} onChange={(event) => setField("channel", event.target.value)}>
              <option value="xiaozhi_official">{t("channels.xiaozhi_official")}</option>
            </select>
          </label>
          <TextField label={t("forms.accessPoint")} value={form.endpoint} onChange={(value) => setField("endpoint", value)} placeholder={isEditing ? t("forms.keepSecret") : "wss://..."} required={!isEditing} />
          <ToggleField label={t("enabled")} checked={form.enabled} onChange={(value) => setField("enabled", value)} />
        </div>
        <div className="form-actions">
          <button className="button-content" disabled={actionId === "upstream" || (!form.endpoint && !editingEndpoint)}>
            <Icon name="save" />
            {actionId === "upstream" ? t("loading") : t("actions.save")}
          </button>
          {isEditing && <button type="button" className="secondary" onClick={reset}>{t("actions.cancel")}</button>}
        </div>
      </form>
      <div className="data-table upstream-table">
        <div className="table-head">
          <span>{t("forms.channel")}</span>
          <span>{t("forms.accessPoint")}</span>
          <span>{t("table.status")}</span>
          <span>{t("table.action")}</span>
        </div>
        {upstreams.map((upstream) => (
          <div className="table-row" key={upstream.id}>
            <strong>{t(`channels.${upstream.channel || upstream.type}`)}</strong>
            <code>{maskEndpoint(upstream.endpoint)}</code>
            <Badge value={upstream.enabled ? "enabled" : "disabled"} kind="status" prefix="status" t={t} />
            <button className="secondary button-content" onClick={() => edit(upstream)}>
              <Icon name="save" />
              {t("actions.edit")}
            </button>
          </div>
        ))}
      </div>
      {!upstreams.length && <EmptyState>{t("empty.upstreams")}</EmptyState>}
    </section>
  );
}

function Servers({ servers, onDiscover, onSave, actionId, t }) {
  const [form, setForm] = useState(blankServer);

  function setField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function submit(event) {
    event.preventDefault();
    onSave(serverPayload(form));
    setForm(blankServer);
  }

  return (
    <section className="section-stack">
      <form className="form-panel" onSubmit={submit}>
        <div className="form-title">
          <Icon name="servers" />
          <div>
            <strong>{t("forms.addServer")}</strong>
            <span>{t("forms.serverHint")}</span>
          </div>
        </div>
        <div className="form-grid">
          <TextField label={t("forms.id")} value={form.id} onChange={(value) => setField("id", value)} required />
          <label>
            {t("table.transport")}
            <select value={form.transport} onChange={(event) => setField("transport", event.target.value)}>
              <option value="stdio">stdio</option>
              <option value="streamable_http">streamable_http</option>
              <option value="sse">sse</option>
            </select>
          </label>
          <TextField label={t("forms.namespace")} value={form.namespace} onChange={(value) => setField("namespace", value)} placeholder={form.id || "home"} required />
          {form.transport === "stdio" ? (
            <>
              <TextField label={t("forms.command")} value={form.command} onChange={(value) => setField("command", value)} placeholder="python" />
              <TextareaField label={t("forms.args")} value={form.argsText} onChange={(value) => setField("argsText", value)} rows={3} placeholder={"../examples/downstream-mcp/demo_server.py"} />
              <TextareaField label={t("forms.env")} value={form.envText} onChange={(value) => setField("envText", value)} rows={3} placeholder="KEY=value" />
            </>
          ) : (
            <>
              <TextField label={t("forms.endpoint")} value={form.endpoint} onChange={(value) => setField("endpoint", value)} placeholder="https://example.com/mcp" />
              <label>
                {t("forms.authType")}
                <select value={form.authType} onChange={(event) => setField("authType", event.target.value)}>
                  <option value="none">none</option>
                  <option value="bearer">bearer</option>
                  <option value="api_key">api_key</option>
                </select>
              </label>
              {form.authType === "bearer" && <TextField label={t("forms.tokenRef")} value={form.tokenRef} onChange={(value) => setField("tokenRef", value)} placeholder="HA_TOKEN" />}
              {form.authType === "api_key" && <TextField label={t("forms.apiKeyRef")} value={form.apiKeyRef} onChange={(value) => setField("apiKeyRef", value)} placeholder="API_KEY" />}
              {form.authType === "api_key" && <TextField label={t("forms.headerName")} value={form.headerName} onChange={(value) => setField("headerName", value)} placeholder="X-API-Key" />}
            </>
          )}
          <TextField label={t("forms.timeout")} type="number" value={form.timeout_ms} onChange={(value) => setField("timeout_ms", Number(value))} />
          <ToggleField label={t("enabled")} checked={form.enabled} onChange={(value) => setField("enabled", value)} />
        </div>
        <details className="advanced-panel">
          <summary>{t("forms.advanced")}</summary>
          <div className="form-grid compact-form-grid">
            <TextField label={t("forms.tenant")} value={form.tenant_id} onChange={(value) => setField("tenant_id", value)} required />
            <TextField label={t("forms.tags")} value={form.tagsText} onChange={(value) => setField("tagsText", value)} placeholder="home,local" />
          </div>
        </details>
        <div className="form-actions">
          <button className="button-content" disabled={actionId === "server" || !form.id || !form.namespace || (form.transport === "stdio" ? !form.command : !form.endpoint)}>
            <Icon name="add" />
            {actionId === "server" ? t("loading") : t("actions.addServer")}
          </button>
        </div>
      </form>
      <div className="data-table server-table">
        <div className="table-head">
          <span>{t("table.server")}</span>
          <span>{t("table.transport")}</span>
          <span>{t("table.status")}</span>
          <span>{t("table.latency")}</span>
          <span>{t("table.action")}</span>
        </div>
        {servers.map((server) => (
          <div className="table-row" key={server.id}>
            <strong>{server.id}</strong>
            <Badge value={server.transport} kind="transport" />
            <Badge value={server.status || "unknown"} kind="status" prefix="status" t={t} />
            <span>{server.latency_ms ? `${Math.round(server.latency_ms)} ms` : t("emptyDash")}</span>
            <button className="button-content" onClick={() => onDiscover(server.id)} disabled={actionId === server.id}>
              <Icon name="refresh" />
              {actionId === server.id ? t("loading") : t("actions.discover")}
            </button>
          </div>
        ))}
      </div>
      {!servers.length && <EmptyState>{t("empty.servers")}</EmptyState>}
    </section>
  );
}

function ConfigImport({ onImport, actionId, importResult, t }) {
  const [raw, setRaw] = useState("");
  const [file, setFile] = useState(null);

  function submit(event) {
    event.preventDefault();
    onImport({ raw, file });
  }

  return (
    <section className="section-stack">
      <form className="form-panel import-panel" onSubmit={submit}>
        <div className="form-title">
          <Icon name="upload" />
          <div>
            <strong>{t("forms.importConfig")}</strong>
            <span>{t("forms.importHint")}</span>
          </div>
        </div>
        <TextareaField label={t("forms.yamlJson")} value={raw} onChange={setRaw} rows={12} placeholder={t("forms.importPlaceholder")} />
        <label className="file-input">
          {t("forms.file")}
          <input type="file" accept=".yaml,.yml,.json,application/json,text/yaml" onChange={(event) => setFile(event.target.files?.[0] || null)} />
          <span>{file ? file.name : t("forms.noFile")}</span>
        </label>
        <div className="form-actions">
          <button className="button-content" disabled={actionId === "import" || (!raw.trim() && !file)}>
            <Icon name="upload" />
            {actionId === "import" ? t("loading") : t("actions.import")}
          </button>
        </div>
      </form>
      {importResult && (
        <div className="notice success">
          {t("config.imported")} {t("stats.upstreams")}: {importResult.upstreams}, {t("stats.servers")}: {importResult.servers}, {t("stats.tools")}: {importResult.tools ?? 0}, {t("config.version")}: {importResult.version}
          {Object.keys(importResult.errors || {}).length > 0 && (
            <pre className="error-list">{JSON.stringify(importResult.errors, null, 2)}</pre>
          )}
        </div>
      )}
    </section>
  );
}

function Tools({ tools, t }) {
  const [copied, setCopied] = useState("");

  async function copy(value) {
    await navigator.clipboard?.writeText(value);
    setCopied(value);
    window.setTimeout(() => setCopied(""), 1200);
  }

  return (
    <section className="tool-grid">
      {tools.map((tool) => (
        <article className="tool-card" key={tool.tool_id}>
          <div className="tool-card-head">
            <strong>{tool.tool_id}</strong>
            <Badge value={tool.risk_level || "low"} kind="risk" prefix="risk" t={t} />
          </div>
          <p>{tool.description || tool.display_name}</p>
          <div className="meta-grid">
            <span>{t("table.server")}</span>
            <strong>{tool.server_id}</strong>
            <span>{t("table.origin")}</span>
            <strong>{tool.origin_tool_name}</strong>
            <span>{t("table.status")}</span>
            <strong>{tool.enabled ? t("enabled") : t("disabled")}</strong>
          </div>
          <button className="secondary" onClick={() => copy(tool.tool_id)}>
            <Icon name="copy" />
            {copied === tool.tool_id ? t("actions.copied") : t("actions.copy")}
          </button>
        </article>
      ))}
      {!tools.length && <EmptyState>{t("empty.tools")}</EmptyState>}
    </section>
  );
}

function Approvals({ approvals, onApprove, onReject, actionId, t }) {
  return (
    <section className="section-band">
      <div className="data-table approval-table">
        <div className="table-head">
          <span>{t("table.tool")}</span>
          <span>{t("table.status")}</span>
          <span>{t("table.requestedAt")}</span>
          <span>{t("table.action")}</span>
        </div>
        {approvals.map((approval) => (
          <div className="table-row" key={approval.id}>
            <strong>{approval.tool_id}</strong>
            <Badge value={approval.status || "pending"} kind="status" prefix="status" t={t} />
            <span>{formatDate(approval.created_at)}</span>
            <span className="button-group">
              <button className="button-content" onClick={() => onApprove(approval.id)} disabled={actionId === approval.id}>
                <Icon name="check" />
                {t("actions.approve")}
              </button>
              <button className="danger button-content" onClick={() => onReject(approval.id)} disabled={actionId === approval.id}>
                <Icon name="x" />
                {t("actions.reject")}
              </button>
            </span>
          </div>
        ))}
      </div>
      {!approvals.length && <EmptyState>{t("empty.approvals")}</EmptyState>}
    </section>
  );
}

function Audit({ audit, t }) {
  return (
    <section className="section-band">
      <div className="data-table audit-table">
        <div className="table-head">
          <span>{t("table.auditAction")}</span>
          <span>{t("table.status")}</span>
          <span>{t("table.tool")}</span>
          <span>{t("table.trace")}</span>
          <span>{t("table.error")}</span>
        </div>
        {audit.map((item) => (
          <div className="table-row" key={item.id}>
            <strong>{item.action}</strong>
            <Badge value={item.status || "unknown"} kind="status" prefix="status" t={t} />
            <span>{item.tool_id || t("emptyDash")}</span>
            <code>{item.trace_id}</code>
            <span>{item.error || t("emptyDash")}</span>
          </div>
        ))}
      </div>
      {!audit.length && <EmptyState>{t("empty.audit")}</EmptyState>}
    </section>
  );
}

function serverPayload(form) {
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

function splitList(value) {
  return String(value || "")
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function parseEnv(value) {
  return String(value || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .reduce((acc, line) => {
      const index = line.indexOf("=");
      if (index > 0) acc[line.slice(0, index).trim()] = line.slice(index + 1).trim();
      return acc;
    }, {});
}

function maskEndpoint(value) {
  if (!value) return "-";
  return value.replace(/([?&][^=]+=)[^&]+/g, "$1***").replace(/(token|key|secret)=([^&]+)/gi, "$1=***");
}

function formatDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString();
}

export default function App() {
  const [locale, setLocale] = useState(detectLocale);
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [active, setActive] = useState("overview");
  const [data, setData] = useState({ summary: {}, upstreams: [], servers: [], tools: [], approvals: [], audit: [] });
  const [user, setUser] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [importResult, setImportResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionId, setActionId] = useState("");
  const t = useMemo(() => createTranslator(locale), [locale]);
  const client = useMemo(() => api(token), [token]);

  function changeLocale(value) {
    localStorage.setItem("locale", value);
    setLocale(value);
  }

  function saveToken(value) {
    localStorage.setItem("token", value);
    setToken(value);
  }

  function signOut() {
    localStorage.removeItem("token");
    setToken("");
    setUser(null);
  }

  async function load() {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const [me, summary, upstreams, servers, tools, approvals, audit] = await Promise.all([
        client.me(),
        client.summary(),
        client.upstreams(),
        client.servers(),
        client.tools(),
        client.approvals(),
        client.audit()
      ]);
      setUser(me);
      setData({ summary, upstreams, servers, tools, approvals, audit });
    } catch (err) {
      if (err.status === 401) {
        localStorage.removeItem("token");
        setToken("");
        setUser(null);
        setError(t("errors.sessionExpired"));
        return;
      }
      setError(t("errors.refresh"));
    } finally {
      setLoading(false);
    }
  }

  async function runAction(id, action, successKey) {
    setActionId(id);
    setError("");
    setMessage("");
    try {
      const result = await action();
      if (id === "import") setImportResult(result);
      if (successKey) setMessage(t(successKey));
      await load();
    } catch (err) {
      setError(t("errors.action"));
    } finally {
      setActionId("");
    }
  }

  useEffect(() => {
    load();
  }, [token, locale]);

  if (!token) {
    return <Login locale={locale} onLocaleChange={changeLocale} onLogin={saveToken} t={t} />;
  }

  return (
    <Shell
      locale={locale}
      onLocaleChange={changeLocale}
      user={user}
      active={active}
      setActive={setActive}
      onRefresh={load}
      onSignOut={signOut}
      loading={loading}
      t={t}
    >
      {error && <div className="notice error">{error}</div>}
      {message && <div className="notice success">{message}</div>}
      {loading && <div className="notice loading">{t("loading")}</div>}
      {active === "overview" && <Overview data={data} t={t} />}
      {active === "upstreams" && (
        <Upstreams
          upstreams={data.upstreams}
          actionId={actionId}
          onSave={(payload) => runAction("upstream", () => client.saveUpstream(payload), "messages.upstreamSaved")}
          t={t}
        />
      )}
      {active === "servers" && (
        <Servers
          servers={data.servers}
          actionId={actionId}
          onSave={(payload) => runAction("server", () => client.saveServer(payload), "messages.serverSaved")}
          onDiscover={(id) => runAction(id, () => client.discover(id), "messages.discovered")}
          t={t}
        />
      )}
      {active === "tools" && <Tools tools={data.tools} t={t} />}
      {active === "config" && (
        <ConfigImport
          actionId={actionId}
          importResult={importResult}
          onImport={(payload) => runAction("import", () => client.importConfig(payload), "messages.imported")}
          t={t}
        />
      )}
      {active === "approvals" && (
        <Approvals
          approvals={data.approvals}
          actionId={actionId}
          onApprove={(id) => runAction(id, () => client.approve(id), "messages.approved")}
          onReject={(id) => runAction(id, () => client.reject(id, t("actions.reject")), "messages.rejected")}
          t={t}
        />
      )}
      {active === "audit" && <Audit audit={data.audit} t={t} />}
    </Shell>
  );
}
