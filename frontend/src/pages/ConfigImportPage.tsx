import { useState, type ChangeEvent, type FormEvent } from "react";
import { EmptyState } from "../components/common/EmptyState";
import { TextareaField } from "../components/common/Fields";
import { Icon } from "../components/common/Icon";
import type { ConfigImportInput, ImportResult, Translator } from "../types";

export function ConfigImportPage({
  onImport,
  result,
  actionId,
  t
}: {
  onImport: (input: ConfigImportInput) => void;
  result: ImportResult | null;
  actionId: string;
  t: Translator;
}) {
  const [raw, setRaw] = useState("");
  const [file, setFile] = useState<File | null>(null);

  function chooseFile(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] || null);
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    // 导入入口同时支持粘贴文本和文件上传，后端会负责 YAML/JSON 解析与最终校验。
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
        <TextareaField label={t("forms.yamlJson")} value={raw} onChange={setRaw} rows={14} placeholder={t("forms.importPlaceholder")} />
        <label className="file-picker">
          {t("forms.file")}
          <input type="file" accept=".yaml,.yml,.json,application/json,text/yaml" onChange={chooseFile} />
          <span>{file?.name || t("forms.noFile")}</span>
        </label>
        <div className="form-actions">
          <button className="button-content" disabled={actionId === "import" || (!raw.trim() && !file)}>
            <Icon name="upload" />
            {actionId === "import" ? t("loading") : t("actions.import")}
          </button>
        </div>
      </form>

      {result ? (
        <article className="result-panel">
          <div className="section-title">
            <Icon name="check" />
            <strong>{t("config.imported")}</strong>
            <span>{t("config.version")}: {result.version}</span>
          </div>
          <div className="dashboard-grid compact-stats">
            <div className="stat-card"><span>{t("sections.upstreams")}</span><strong>{result.upstreams}</strong></div>
            <div className="stat-card"><span>{t("sections.servers")}</span><strong>{result.servers}</strong></div>
            <div className="stat-card"><span>{t("sections.tools")}</span><strong>{result.tools ?? 0}</strong></div>
          </div>
          {result.errors && Object.keys(result.errors).length > 0 && (
            <div className="notice error import-errors">
              {Object.entries(result.errors).map(([id, message]) => (
                <p key={id}><strong>{id}</strong>: {message}</p>
              ))}
            </div>
          )}
        </article>
      ) : (
        <EmptyState>{t("forms.importHint")}</EmptyState>
      )}
    </section>
  );
}
