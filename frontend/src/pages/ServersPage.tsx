import { useMemo, useState, type FormEvent } from "react";
import type { ApiClient } from "../api/client";
import { blankServer } from "../forms";
import { Badge } from "../components/common/Badge";
import { EmptyState } from "../components/common/EmptyState";
import { TextareaField, TextField, ToggleField } from "../components/common/Fields";
import { Icon } from "../components/common/Icon";
import type { DownstreamServer, ServerFormState, Translator, TransportType } from "../types";
import { serverPayload } from "../utils/format";

const transports: TransportType[] = ["stdio", "streamable_http", "sse"];

export function ServersPage({
  servers,
  onSave,
  onDiscover,
  actionId,
  t
}: {
  servers: DownstreamServer[];
  onSave: (payload: ReturnType<typeof serverPayload>) => void;
  onDiscover: (serverId: string) => void;
  actionId: string;
  t: Translator;
}) {
  const [form, setForm] = useState<ServerFormState>(blankServer);
  const requiresEndpoint = form.transport !== "stdio";
  const canSubmit = Boolean(form.id.trim() && form.namespace.trim() && (requiresEndpoint ? form.endpoint.trim() : form.command.trim()));

  function setField<K extends keyof ServerFormState>(field: K, value: ServerFormState[K]) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function edit(server: DownstreamServer) {
    setForm({
      ...blankServer,
      id: server.id,
      namespace: server.namespace,
      tenant_id: server.tenant_id || "default",
      transport: (server.transport as TransportType) || "stdio",
      endpoint: server.endpoint || "",
      command: server.command || "",
      enabled: server.enabled
    });
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    onSave(serverPayload(form));
    setForm(blankServer);
  }

  const activeServers = useMemo(() => servers.filter((server) => server.enabled).length, [servers]);

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
        <div className="form-tabs">
          {transports.map((transport) => (
            <button key={transport} type="button" className={form.transport === transport ? "tab active" : "tab"} onClick={() => setField("transport", transport)}>
              {transport}
            </button>
          ))}
        </div>
        <div className="form-grid">
          <TextField label={t("forms.id")} value={form.id} onChange={(value) => setField("id", value)} required />
          <TextField label={t("forms.namespace")} value={form.namespace} onChange={(value) => setField("namespace", value)} required />
          <TextField label={t("forms.tenant")} value={form.tenant_id} onChange={(value) => setField("tenant_id", value)} />
          {form.transport === "stdio" ? (
            <>
              <TextField label={t("forms.command")} value={form.command} onChange={(value) => setField("command", value)} placeholder="python" required />
              <TextareaField label={t("forms.args")} value={form.argsText} onChange={(value) => setField("argsText", value)} rows={3} />
              <TextareaField label={t("forms.env")} value={form.envText} onChange={(value) => setField("envText", value)} rows={3} />
            </>
          ) : (
            <>
              <TextField label={t("forms.endpoint")} value={form.endpoint} onChange={(value) => setField("endpoint", value)} placeholder="https://example.com/mcp" required />
              <label>
                {t("forms.authType")}
                <select value={form.authType} onChange={(event) => setField("authType", event.target.value as ServerFormState["authType"])}>
                  <option value="none">none</option>
                  <option value="bearer">bearer</option>
                  <option value="api_key">api_key</option>
                </select>
              </label>
              {form.authType === "bearer" && <TextField label={t("forms.tokenRef")} value={form.tokenRef} onChange={(value) => setField("tokenRef", value)} />}
              {form.authType === "api_key" && (
                <>
                  <TextField label={t("forms.apiKeyRef")} value={form.apiKeyRef} onChange={(value) => setField("apiKeyRef", value)} />
                  <TextField label={t("forms.headerName")} value={form.headerName} onChange={(value) => setField("headerName", value)} placeholder="X-API-Key" />
                </>
              )}
            </>
          )}
          <TextField label={t("forms.timeout")} type="number" value={form.timeout_ms} onChange={(value) => setField("timeout_ms", Number(value))} />
          <TextField label={t("forms.tags")} value={form.tagsText} onChange={(value) => setField("tagsText", value)} />
          <ToggleField label={t("enabled")} checked={form.enabled} onChange={(value) => setField("enabled", value)} />
        </div>
        <div className="form-actions">
          <button className="button-content" disabled={actionId === "server" || !canSubmit}>
            <Icon name="save" />
            {actionId === "server" ? t("loading") : t("actions.addServer")}
          </button>
        </div>
      </form>

      <div className="section-title">
        <Icon name="servers" />
        <strong>{t("sections.servers")}</strong>
        <span>{activeServers}/{servers.length}</span>
      </div>
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
            <div>
              <strong>{server.id}</strong>
              <code>{server.namespace}</code>
            </div>
            <span>{server.transport}</span>
            <div className="inline-badges">
              <Badge value={server.status || "unknown"} kind="status" prefix="status" t={t} />
              <Badge value={server.enabled ? "enabled" : "disabled"} kind="status" prefix="status" t={t} />
            </div>
            <span>{server.latency_ms == null ? "-" : `${server.latency_ms} ms`}</span>
            <div className="row-actions">
              <button className="secondary button-content" onClick={() => edit(server)}>
                <Icon name="save" />
                {t("actions.edit")}
              </button>
              <button className="secondary button-content" onClick={() => onDiscover(server.id)} disabled={actionId === `discover:${server.id}`}>
                <Icon name="refresh" />
                {actionId === `discover:${server.id}` ? t("loading") : t("actions.discover")}
              </button>
            </div>
          </div>
        ))}
      </div>
      {!servers.length && <EmptyState>{t("empty.servers")}</EmptyState>}
    </section>
  );
}

export type ServersApi = Pick<ApiClient, "saveServer" | "discover">;
