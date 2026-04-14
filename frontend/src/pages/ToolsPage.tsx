import { useState } from "react";
import { Badge } from "../components/common/Badge";
import { EmptyState } from "../components/common/EmptyState";
import { Icon } from "../components/common/Icon";
import type { ToolRecord, Translator } from "../types";

export function ToolsPage({ tools, t }: { tools: ToolRecord[]; t: Translator }) {
  const [copied, setCopied] = useState("");

  async function copyToolId(toolId: string) {
    // 复制失败不影响主流程，主要用于让长 tool_id 更容易粘贴到调试请求里。
    await navigator.clipboard?.writeText(toolId).catch(() => undefined);
    setCopied(toolId);
    window.setTimeout(() => setCopied(""), 1200);
  }

  return (
    <section className="section-stack">
      <div className="data-table tools-table">
        <div className="table-head">
          <span>{t("table.tool")}</span>
          <span>{t("table.server")}</span>
          <span>{t("table.risk")}</span>
          <span>{t("table.status")}</span>
          <span>{t("table.action")}</span>
        </div>
        {tools.map((tool) => (
          <div className="table-row" key={tool.tool_id}>
            <div className="tool-cell">
              <strong className="tool-name">{tool.display_name || tool.tool_id}</strong>
              <code>{tool.tool_id}</code>
              {tool.description && <span className="tool-description">{tool.description}</span>}
            </div>
            <div className="server-cell">
              <strong>{tool.server_id}</strong>
              <code>{tool.origin_tool_name}</code>
            </div>
            <Badge value={tool.risk_level || "low"} kind="risk" prefix="risk" t={t} />
            <Badge value={tool.enabled ? "enabled" : "disabled"} kind="status" prefix="status" t={t} />
            <button className="secondary button-content" onClick={() => copyToolId(tool.tool_id)}>
              <Icon name="copy" />
              {copied === tool.tool_id ? t("actions.copied") : t("actions.copy")}
            </button>
          </div>
        ))}
      </div>
      {!tools.length && <EmptyState>{t("empty.tools")}</EmptyState>}
    </section>
  );
}
