import type { ReactNode } from "react";
import { MARK_IMAGE } from "../../assets";
import type { ActivePage, Locale, Translator, User } from "../../types";
import { Icon } from "../common/Icon";
import { LanguageSelect } from "../common/LanguageSelect";

const navItems: ActivePage[] = ["overview", "upstreams", "servers", "tools", "config", "approvals", "audit"];

export function Shell({
  locale,
  onLocaleChange,
  user,
  active,
  setActive,
  onRefresh,
  onSignOut,
  loading,
  t,
  children
}: {
  locale: Locale;
  onLocaleChange: (locale: Locale) => void;
  user: User | null;
  active: ActivePage;
  setActive: (page: ActivePage) => void;
  onRefresh: () => void;
  onSignOut: () => void;
  loading: boolean;
  t: Translator;
  children: ReactNode;
}) {
  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand-row">
          <img src={MARK_IMAGE} alt="" className="nav-mark" />
          <div>
            <strong>{t("product")}</strong>
            <span>{t("header.signedIn")}</span>
          </div>
        </div>
        <div className="account-card">
          <strong>{user?.email || t("loading")}</strong>
          <span>{t("header.tenant")}: {user?.tenant_id || "default"}</span>
          <span>{t("header.role")}: {user?.role || t("unknown")}</span>
        </div>
        <nav className="nav-list">
          {navItems.map((item) => (
            <button key={item} className={active === item ? "nav-item active" : "nav-item"} onClick={() => setActive(item)}>
              <Icon name={item} />
              <span>{t(`nav.${item}`)}</span>
            </button>
          ))}
        </nav>
      </aside>
      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">{t("header.title")}</p>
            <h1>{t(`sections.${active}`)}</h1>
            <p>{t("header.subtitle")}</p>
          </div>
          <div className="topbar-actions">
            <LanguageSelect locale={locale} onLocaleChange={onLocaleChange} t={t} />
            <button className="secondary button-content" onClick={onRefresh} disabled={loading}>
              <Icon name="refresh" />
              <span>{loading ? t("refreshing") : t("refresh")}</span>
            </button>
            <button className="ghost button-content" onClick={onSignOut}>
              <Icon name="logout" />
              <span>{t("signOut")}</span>
            </button>
          </div>
        </header>
        {children}
      </section>
    </main>
  );
}

