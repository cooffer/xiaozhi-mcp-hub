import { LOCALES } from "../../i18n";
import type { Locale, Translator } from "../../types";
import { Icon } from "./Icon";

export function LanguageSelect({ locale, onLocaleChange, t }: { locale: Locale; onLocaleChange: (locale: Locale) => void; t: Translator }) {
  return (
    <label className="language-select">
      <span><Icon name="language" />{t("language")}</span>
      <select value={locale} onChange={(event) => onLocaleChange(event.target.value as Locale)}>
        {LOCALES.map((item) => (
          <option key={item} value={item}>
            {item === "zh-CN" ? "中文" : "English"}
          </option>
        ))}
      </select>
    </label>
  );
}

