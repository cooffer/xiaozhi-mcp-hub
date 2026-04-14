import { Badge } from "../components/common/Badge";
import { EmptyState } from "../components/common/EmptyState";
import type { AuditLog, Translator } from "../types";

export function AuditPage({ audit, t }: { audit: AuditLog[]; t: Translator }) {
  return (
    <section className="section-stack">
      <div className="data-table audit-table">
        <div className="table-head">
          <span>{t("table.trace")}</span>
          <span>{t("table.auditAction")}</span>
          <span>{t("table.status")}</span>
          <span>{t("table.tool")}</span>
          <span>{t("table.error")}</span>
        </div>
        {audit.map((item) => (
          <div className="table-row" key={item.id}>
            <code>{item.trace_id}</code>
            <span>{item.action}</span>
            <Badge value={item.status || "unknown"} kind="status" prefix="status" t={t} />
            <strong>{item.tool_id || "-"}</strong>
            <span className={item.error ? "error-text" : ""}>{item.error || "-"}</span>
          </div>
        ))}
      </div>
      {!audit.length && <EmptyState>{t("empty.audit")}</EmptyState>}
    </section>
  );
}
