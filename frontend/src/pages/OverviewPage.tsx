import type { CSSProperties } from "react";
import { EmptyState } from "../components/common/EmptyState";
import { Icon } from "../components/common/Icon";
import { Stat } from "../components/common/Stat";
import type { DashboardData, Translator } from "../types";

export function OverviewPage({ data, t }: { data: DashboardData; t: Translator }) {
  return (
    <section className="overview-layout">
      <div className="dashboard-grid">
        <Stat label={t("stats.upstreams")} value={data.upstreams.length} detail={t("sections.upstreams")} />
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
          <div className="donut" style={{ "--high": `${Math.min(75, (data.summary.pending_approvals || 0) * 12)}deg` } as CSSProperties} />
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
