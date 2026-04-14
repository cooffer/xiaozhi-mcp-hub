export const LOCALES = ["zh-CN", "en-US"] as const;

export type Locale = (typeof LOCALES)[number];
export type Translator = (path: string) => string;

const dictionaries = {
  "zh-CN": {
    product: "Xiaozhi MCP Hub",
    language: "语言",
    refresh: "刷新",
    refreshing: "刷新中",
    signOut: "退出登录",
    loading: "加载中",
    unknown: "未知",
    enabled: "已启用",
    disabled: "已停用",
    active: "运行中",
    inactive: "未启用",
    emptyDash: "-",
    channels: {
      xiaozhi_official: "小智官方"
    },
    login: {
      eyebrow: "MCP 聚合网关",
      title: "把小智接入每一个可信工具",
      subtitle: "统一管理下游 MCP 服务、工具权限、高危审批与调用审计。",
      point1: "统一工具目录",
      point2: "高危操作审批",
      point3: "调用链路审计",
      email: "账号 / 邮箱",
      password: "密码",
      submit: "登录",
      signInTab: "登录",
      registerTab: "首次注册",
      registerTitle: "创建首个管理员",
      registerHint: "当前数据库还没有管理员。第一个注册用户会成为后台管理员，之后公开注册会自动关闭。",
      registerSubmit: "创建管理员",
      error: "登录失败，请检查账号或密码。",
      registerError: "注册失败。请确认密码至少 8 位，且当前仍允许首次注册。",
      hint: "如果已创建管理员，请使用管理员账号登录。",
      previewTitle: "实时治理链路",
      previewStep1: "小智接入点",
      previewStep2: "工具注册中心",
      previewStep3: "审批与审计",
      previewMetric1: "已治理工具",
      previewMetric2: "审计覆盖"
    },
    nav: {
      overview: "概览",
      upstreams: "小智接入",
      servers: "下游服务",
      tools: "暴露工具",
      config: "配置导入",
      approvals: "审批",
      audit: "审计"
    },
    header: {
      title: "运维控制台",
      subtitle: "统一观察小智接入点、下游服务、暴露工具、审批队列与调用审计。",
      tenant: "租户",
      role: "角色",
      signedIn: "当前账号"
    },
    stats: {
      upstreams: "接入点",
      servers: "下游服务",
      tools: "暴露工具",
      healthy: "健康实例",
      pending: "待审批"
    },
    sections: {
      overview: "运行概览",
      upstreams: "小智官方接入",
      servers: "下游 MCP 服务",
      tools: "暴露给小智的工具",
      config: "配置导入",
      approvals: "高危审批",
      audit: "调用审计",
      systemMap: "治理链路",
      recentRisk: "风险分布"
    },
    overview: {
      upstream: "小智官方",
      hub: "MCP Hub",
      downstream: "下游服务",
      policy: "策略层",
      audit: "审计日志"
    },
    table: {
      upstream: "上游",
      endpoint: "接入点",
      tenant: "租户",
      server: "服务",
      transport: "传输",
      status: "状态",
      latency: "延迟",
      action: "操作",
      tool: "工具",
      risk: "风险",
      origin: "原始工具",
      approval: "审批单",
      requestedAt: "创建时间",
      auditAction: "动作",
      trace: "Trace ID",
      error: "错误"
    },
    forms: {
      id: "服务 ID",
      channel: "渠道（厂商）",
      accessPoint: "接入点",
      tenant: "租户",
      endpoint: "服务地址",
      keepSecret: "留空则保留当前接入点",
      addXiaozhi: "新增小智接入点",
      editXiaozhi: "编辑小智接入点",
      upstreamHint: "从小智后台复制 MCP 接入点粘贴到这里。保存启用后，Hub 会作为 MCP Server 连接小智官方服务。",
      addServer: "新增下游 MCP 服务",
      serverHint: "下游服务会被发现为工具，并通过 Hub 暴露给小智。批量接入建议使用配置导入。",
      namespace: "命名空间",
      command: "命令",
      args: "参数，每行或逗号分隔",
      env: "环境变量，每行 KEY=value",
      authType: "认证类型",
      tokenRef: "Bearer token 引用",
      apiKeyRef: "API key 引用",
      headerName: "API key Header",
      timeout: "超时 ms",
      tags: "标签，逗号分隔",
      advanced: "高级配置",
      importConfig: "导入 YAML/JSON 配置",
      importHint: "支持项目原生 servers 列表，也支持常见 mcpServers 配置。导入后会自动发现工具。",
      yamlJson: "YAML / JSON 内容",
      importPlaceholder: "{\n  \"mcpServers\": {\n    \"demo\": {\n      \"command\": \"python.exe\",\n      \"args\": [\"../examples/downstream-mcp/demo_server.py\"]\n    }\n  }\n}",
      file: "配置文件",
      noFile: "未选择文件"
    },
    config: {
      imported: "导入完成。",
      version: "配置版本"
    },
    actions: {
      discover: "发现工具",
      approve: "批准",
      reject: "拒绝",
      copy: "复制",
      copied: "已复制",
      save: "保存",
      edit: "编辑",
      cancel: "取消",
      addServer: "新增服务",
      import: "导入配置"
    },
    messages: {
      upstreamSaved: "小智接入点已保存。",
      serverSaved: "下游服务已保存。",
      discovered: "工具发现已完成。",
      imported: "配置导入已完成。",
      approved: "审批已批准。",
      rejected: "审批已拒绝。"
    },
    empty: {
      upstreams: "还没有小智接入点。请从小智后台复制 MCP 接入点后新增。",
      servers: "还没有下游 MCP 服务。可以手动新增或导入配置。",
      tools: "还没有暴露工具。请先导入服务或对下游服务执行发现。",
      approvals: "暂无待处理审批。",
      audit: "暂无审计记录。",
      overview: "运行数据会在连接小智接入点和下游服务后出现。"
    },
    errors: {
      refresh: "无法刷新 Hub 状态，请确认后端服务正在运行。",
      action: "操作失败，请检查输入或稍后重试。",
      sessionExpired: "登录状态已过期，请重新登录。"
    },
    risk: {
      low: "低",
      medium: "中",
      high: "高",
      critical: "严重"
    },
    status: {
      enabled: "已启用",
      disabled: "已停用",
      healthy: "健康",
      degraded: "降级",
      down: "离线",
      circuit_open: "熔断",
      unknown: "未知",
      pending: "待处理",
      approved: "已批准",
      rejected: "已拒绝",
      expired: "已过期",
      ok: "成功",
      error: "错误",
      denied: "已拒绝",
      approval_pending: "待审批",
      approval_rejected: "审批拒绝",
      route_not_found: "无路由"
    }
  },
  "en-US": {
    product: "Xiaozhi MCP Hub",
    language: "Language",
    refresh: "Refresh",
    refreshing: "Refreshing",
    signOut: "Sign out",
    loading: "Loading",
    unknown: "Unknown",
    enabled: "Enabled",
    disabled: "Disabled",
    active: "Active",
    inactive: "Inactive",
    emptyDash: "-",
    channels: {
      xiaozhi_official: "Xiaozhi Official"
    },
    login: {
      eyebrow: "MCP aggregation gateway",
      title: "Connect Xiaozhi to every trusted tool",
      subtitle: "Govern downstream MCP services, tool access, high-risk approvals and audit trails.",
      point1: "Unified tool registry",
      point2: "High-risk approvals",
      point3: "Audited tool calls",
      email: "Account / email",
      password: "Password",
      submit: "Sign in",
      signInTab: "Sign in",
      registerTab: "First setup",
      registerTitle: "Create the first administrator",
      registerHint: "No administrator exists yet. The first registered user becomes admin and public registration closes afterwards.",
      registerSubmit: "Create administrator",
      error: "Login failed. Check the account or password.",
      registerError: "Registration failed. Use a password with at least 8 characters and make sure first setup is still open.",
      hint: "Use an administrator account after first setup is complete.",
      previewTitle: "Live governance path",
      previewStep1: "Xiaozhi endpoint",
      previewStep2: "Tool registry",
      previewStep3: "Approvals and audit",
      previewMetric1: "Governed tools",
      previewMetric2: "Audit coverage"
    },
    nav: {
      overview: "Overview",
      upstreams: "Xiaozhi",
      servers: "Servers",
      tools: "Exposed Tools",
      config: "Import",
      approvals: "Approvals",
      audit: "Audit"
    },
    header: {
      title: "Operations",
      subtitle: "Watch Xiaozhi endpoints, downstream services, exposed tools, approvals and audit in one place.",
      tenant: "Tenant",
      role: "Role",
      signedIn: "Signed in"
    },
    stats: {
      upstreams: "Endpoints",
      servers: "Servers",
      tools: "Exposed tools",
      healthy: "Healthy",
      pending: "Pending approvals"
    },
    sections: {
      overview: "Runtime Overview",
      upstreams: "Xiaozhi Official Access",
      servers: "Downstream MCP Servers",
      tools: "Tools Exposed to Xiaozhi",
      config: "Config Import",
      approvals: "High-Risk Approvals",
      audit: "Audit Trail",
      systemMap: "Governance Path",
      recentRisk: "Risk Mix"
    },
    overview: {
      upstream: "Xiaozhi official",
      hub: "MCP Hub",
      downstream: "Downstream servers",
      policy: "Policy layer",
      audit: "Audit logs"
    },
    table: {
      upstream: "Upstream",
      endpoint: "Endpoint",
      tenant: "Tenant",
      server: "Server",
      transport: "Transport",
      status: "Status",
      latency: "Latency",
      action: "Action",
      tool: "Tool",
      risk: "Risk",
      origin: "Origin tool",
      approval: "Approval",
      requestedAt: "Requested",
      auditAction: "Action",
      trace: "Trace ID",
      error: "Error"
    },
    forms: {
      id: "Server ID",
      channel: "Channel",
      accessPoint: "Access point",
      tenant: "Tenant",
      endpoint: "Service URL",
      keepSecret: "Leave blank to keep the current endpoint",
      addXiaozhi: "Add Xiaozhi endpoint",
      editXiaozhi: "Edit Xiaozhi endpoint",
      upstreamHint: "Paste the MCP access point from the Xiaozhi console. When enabled, the hub connects as an MCP server.",
      addServer: "Add downstream MCP server",
      serverHint: "Downstream servers are discovered as tools and exposed to Xiaozhi through the hub. Use import for bulk setup.",
      namespace: "Namespace",
      command: "Command",
      args: "Args, one per line or comma separated",
      env: "Environment, one KEY=value per line",
      authType: "Auth type",
      tokenRef: "Bearer token ref",
      apiKeyRef: "API key ref",
      headerName: "API key header",
      timeout: "Timeout ms",
      tags: "Tags, comma separated",
      advanced: "Advanced",
      importConfig: "Import YAML/JSON config",
      importHint: "Supports native servers lists and common mcpServers configs. Enabled services are discovered after import.",
      yamlJson: "YAML / JSON content",
      importPlaceholder: "{\n  \"mcpServers\": {\n    \"demo\": {\n      \"command\": \"python.exe\",\n      \"args\": [\"../examples/downstream-mcp/demo_server.py\"]\n    }\n  }\n}",
      file: "Config file",
      noFile: "No file selected"
    },
    config: {
      imported: "Import complete.",
      version: "Config version"
    },
    actions: {
      discover: "Discover",
      approve: "Approve",
      reject: "Reject",
      copy: "Copy",
      copied: "Copied",
      save: "Save",
      edit: "Edit",
      cancel: "Cancel",
      addServer: "Add server",
      import: "Import config"
    },
    messages: {
      upstreamSaved: "Xiaozhi endpoint saved.",
      serverSaved: "Downstream server saved.",
      discovered: "Tool discovery finished.",
      imported: "Configuration imported.",
      approved: "Approval accepted.",
      rejected: "Approval rejected."
    },
    empty: {
      upstreams: "No Xiaozhi endpoint yet. Paste the official MCP endpoint from the Xiaozhi console.",
      servers: "No downstream MCP servers yet. Add one manually or import a config.",
      tools: "No exposed tools yet. Import a server or run discovery first.",
      approvals: "No pending decisions.",
      audit: "No audit records yet.",
      overview: "Runtime data appears after connecting Xiaozhi and downstream services."
    },
    errors: {
      refresh: "Could not refresh hub state. Make sure the backend is running.",
      action: "Action failed. Check the input and try again.",
      sessionExpired: "Your session expired. Please sign in again."
    },
    risk: {
      low: "Low",
      medium: "Medium",
      high: "High",
      critical: "Critical"
    },
    status: {
      enabled: "Enabled",
      disabled: "Disabled",
      healthy: "Healthy",
      degraded: "Degraded",
      down: "Down",
      circuit_open: "Circuit open",
      unknown: "Unknown",
      pending: "Pending",
      approved: "Approved",
      rejected: "Rejected",
      expired: "Expired",
      ok: "OK",
      error: "Error",
      denied: "Denied",
      approval_pending: "Approval pending",
      approval_rejected: "Approval rejected",
      route_not_found: "No route"
    }
  }
} as const;

export function detectLocale(): Locale {
  const saved = localStorage.getItem("locale");
  if (saved && (LOCALES as readonly string[]).includes(saved)) return saved as Locale;
  return navigator.language?.toLowerCase().startsWith("zh") ? "zh-CN" : "en-US";
}

export function createTranslator(locale: Locale): Translator {
  const dictionary = dictionaries[locale] || dictionaries["en-US"];
  return function t(path) {
    const value = path.split(".").reduce<unknown>((current, key) => (current as Record<string, unknown> | undefined)?.[key], dictionary);
    return typeof value === "string" ? value : path;
  };
}
