import { useState, type FormEvent } from "react";
import { blankUpstream } from "../forms";
import { Badge } from "../components/common/Badge";
import { EmptyState } from "../components/common/EmptyState";
import { TextField, ToggleField } from "../components/common/Fields";
import { Icon } from "../components/common/Icon";
import type { Translator, Upstream, UpstreamPayload } from "../types";
import { maskEndpoint } from "../utils/format";

export function UpstreamsPage({ upstreams, onSave, actionId, t }: { upstreams: Upstream[]; onSave: (payload: UpstreamPayload) => void; actionId: string; t: Translator }) {
  const [form, setForm] = useState(blankUpstream);
  const [editingEndpoint, setEditingEndpoint] = useState("");
  const isEditing = Boolean(editingEndpoint);

  function setField(field: keyof typeof blankUpstream, value: string | boolean) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function edit(upstream: Upstream) {
    setEditingEndpoint(upstream.endpoint);
    setForm({ ...blankUpstream, id: upstream.id, channel: upstream.channel || upstream.type || "xiaozhi_official", type: upstream.channel || upstream.type || "xiaozhi_official", endpoint: "", enabled: upstream.enabled });
  }

  function reset() {
    setEditingEndpoint("");
    setForm(blankUpstream);
  }

  function submit(event: FormEvent) {
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
