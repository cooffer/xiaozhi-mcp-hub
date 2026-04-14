import { useEffect, useState, type FormEvent } from "react";
import { createApiClient } from "../api/client";
import { MARK_IMAGE } from "../assets";
import { Badge } from "../components/common/Badge";
import { Icon } from "../components/common/Icon";
import { LanguageSelect } from "../components/common/LanguageSelect";
import { TextField } from "../components/common/Fields";
import type { Locale, Translator } from "../types";

export function LoginPage({ locale, onLocaleChange, onLogin, t }: { locale: Locale; onLocaleChange: (locale: Locale) => void; onLogin: (token: string) => void; t: Translator }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [bootstrap, setBootstrap] = useState({ registration_open: false });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let alive = true;
    createApiClient()
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

  async function submitLogin(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const result = await createApiClient().login(email, password);
      onLogin(result.access_token);
    } catch {
      setError(t("login.error"));
    } finally {
      setSubmitting(false);
    }
  }

  async function submitRegister(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const result = await createApiClient().register(registerEmail, registerPassword);
      onLogin(result.access_token);
    } catch {
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
