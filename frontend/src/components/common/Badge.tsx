import type { Translator } from "../../types";

export function Badge({ value, kind = "neutral", t, prefix }: { value: string; kind?: string; t?: Translator; prefix?: string }) {
  const label = prefix && t ? t(`${prefix}.${value}`) : value;
  return <span className={`badge badge-${kind} badge-${String(value).replaceAll("_", "-")}`}>{label || value}</span>;
}

