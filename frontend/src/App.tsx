import { useEffect, useMemo, useState } from "react";
import { ApiRequestError, createApiClient } from "./api/client";
import { Shell } from "./components/layout/Shell";
import { detectLocale, createTranslator } from "./i18n";
import { AuditPage } from "./pages/AuditPage";
import { ApprovalsPage } from "./pages/ApprovalsPage";
import { ConfigImportPage } from "./pages/ConfigImportPage";
import { LoginPage } from "./pages/LoginPage";
import { OverviewPage } from "./pages/OverviewPage";
import { ServersPage } from "./pages/ServersPage";
import { ToolsPage } from "./pages/ToolsPage";
import { UpstreamsPage } from "./pages/UpstreamsPage";
import type { ActivePage, ConfigImportInput, DashboardData, ImportResult, Locale, ServerPayload, UpstreamPayload, User } from "./types";

const emptyData: DashboardData = {
  summary: {},
  upstreams: [],
  servers: [],
  tools: [],
  approvals: [],
  audit: []
};

export default function App() {
  const [locale, setLocale] = useState<Locale>(() => detectLocale());
  const [token, setToken] = useState(() => localStorage.getItem("token") || "");
  const [user, setUser] = useState<User | null>(null);
  const [active, setActive] = useState<ActivePage>("overview");
  const [data, setData] = useState<DashboardData>(emptyData);
  const [loading, setLoading] = useState(false);
  const [actionId, setActionId] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [importResult, setImportResult] = useState<ImportResult | null>(null);

  const t = useMemo(() => createTranslator(locale), [locale]);
  const client = useMemo(() => createApiClient(token), [token]);

  function changeLocale(nextLocale: Locale) {
    localStorage.setItem("locale", nextLocale);
    setLocale(nextLocale);
  }

  function acceptLogin(nextToken: string) {
    localStorage.setItem("token", nextToken);
    setToken(nextToken);
  }

  function signOut() {
    localStorage.removeItem("token");
    setToken("");
    setUser(null);
    setData(emptyData);
  }

  async function refresh() {
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
    } catch (caught) {
      if (caught instanceof ApiRequestError && caught.status === 401) {
        setError(t("errors.sessionExpired"));
        signOut();
      } else {
        setError(t("errors.refresh"));
      }
    } finally {
      setLoading(false);
    }
  }

  async function runAction(id: string, task: () => Promise<unknown>, successKey: string) {
    setActionId(id);
    setError("");
    setNotice("");
    try {
      await task();
      setNotice(t(successKey));
      await refresh();
    } catch {
      setError(t("errors.action"));
    } finally {
      setActionId("");
    }
  }

  function saveUpstream(payload: UpstreamPayload) {
    void runAction("upstream", () => client.saveUpstream(payload), "messages.upstreamSaved");
  }

  function saveServer(payload: ServerPayload) {
    void runAction("server", () => client.saveServer(payload), "messages.serverSaved");
  }

  function discover(serverId: string) {
    void runAction(`discover:${serverId}`, () => client.discover(serverId), "messages.discovered");
  }

  function approve(id: string) {
    void runAction(`approve:${id}`, () => client.approve(id), "messages.approved");
  }

  function reject(id: string) {
    const reason = window.prompt(t("actions.reject")) || "";
    void runAction(`reject:${id}`, () => client.reject(id, reason), "messages.rejected");
  }

  function importConfig(input: ConfigImportInput) {
    void runAction(
      "import",
      async () => {
        // 保存导入结果供页面展示，列表刷新仍统一走 refresh，避免多个页面状态各自漂移。
        const result = await client.importConfig(input);
        setImportResult(result);
      },
      "messages.imported"
    );
  }

  useEffect(() => {
    void refresh();
  }, [token]);

  if (!token) {
    return <LoginPage locale={locale} onLocaleChange={changeLocale} onLogin={acceptLogin} t={t} />;
  }

  const page = {
    overview: <OverviewPage data={data} t={t} />,
    upstreams: <UpstreamsPage upstreams={data.upstreams} onSave={saveUpstream} actionId={actionId} t={t} />,
    servers: <ServersPage servers={data.servers} onSave={saveServer} onDiscover={discover} actionId={actionId} t={t} />,
    tools: <ToolsPage tools={data.tools} t={t} />,
    config: <ConfigImportPage onImport={importConfig} result={importResult} actionId={actionId} t={t} />,
    approvals: <ApprovalsPage approvals={data.approvals} onApprove={approve} onReject={reject} actionId={actionId} t={t} />,
    audit: <AuditPage audit={data.audit} t={t} />
  }[active];

  return (
    <Shell
      locale={locale}
      onLocaleChange={changeLocale}
      user={user}
      active={active}
      setActive={setActive}
      onRefresh={refresh}
      onSignOut={signOut}
      loading={loading}
      t={t}
    >
      {error && <div className="notice error">{error}</div>}
      {notice && <div className="notice success">{notice}</div>}
      {page}
    </Shell>
  );
}
