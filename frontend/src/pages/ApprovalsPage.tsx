import { Badge } from "../components/common/Badge";
import { EmptyState } from "../components/common/EmptyState";
import { Icon } from "../components/common/Icon";
import type { Approval, Translator } from "../types";
import { formatDate } from "../utils/format";

export function ApprovalsPage({
  approvals,
  onApprove,
  onReject,
  actionId,
  t
}: {
  approvals: Approval[];
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
  actionId: string;
  t: Translator;
}) {
  return (
    <section className="section-stack">
      <div className="data-table approvals-table">
        <div className="table-head">
          <span>{t("table.approval")}</span>
          <span>{t("table.tool")}</span>
          <span>{t("table.status")}</span>
          <span>{t("table.requestedAt")}</span>
          <span>{t("table.action")}</span>
        </div>
        {approvals.map((approval) => (
          <div className="table-row" key={approval.id}>
            <code>{approval.id}</code>
            <strong>{approval.tool_id}</strong>
            <Badge value={approval.status} kind="status" prefix="status" t={t} />
            <span>{formatDate(approval.created_at)}</span>
            <div className="row-actions">
              <button className="secondary button-content" disabled={actionId === `approve:${approval.id}` || approval.status !== "pending"} onClick={() => onApprove(approval.id)}>
                <Icon name="check" />
                {t("actions.approve")}
              </button>
              <button className="danger button-content" disabled={actionId === `reject:${approval.id}` || approval.status !== "pending"} onClick={() => onReject(approval.id)}>
                <Icon name="x" />
                {t("actions.reject")}
              </button>
            </div>
          </div>
        ))}
      </div>
      {!approvals.length && <EmptyState>{t("empty.approvals")}</EmptyState>}
    </section>
  );
}
