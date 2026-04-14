export function Stat({ label, value, detail }: { label: string; value: number; detail?: string }) {
  return (
    <article className="stat">
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
      <svg className="sparkline" viewBox="0 0 120 36" aria-hidden="true">
        <path d="M4 27 C18 16 28 20 40 13 S62 9 76 18 96 31 116 10" />
      </svg>
      {detail && <small>{detail}</small>}
    </article>
  );
}

