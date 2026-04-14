const ICONS = {
  overview: "M4 13.5 12 5l8 8.5M6 12.5V20h12v-7.5M9 20v-6h6v6",
  upstreams: "M12 4v16M5 8h6M5 16h6M13 8h6M13 16h6M5 8l-2 2 2 2M19 16l2-2-2-2",
  servers: "M5 6.5h14M5 12h14M5 17.5h14M7 4h10a2 2 0 0 1 2 2v1a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Zm0 6h10a2 2 0 0 1 2 2v1a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-1a2 2 0 0 1 2-2Zm0 6h10a2 2 0 0 1 2 2v1a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-1a2 2 0 0 1 2-2Z",
  tools: "M14.5 5.5 18 2l4 4-3.5 3.5M14.5 5.5l4 4M14.5 5.5 4 16v4h4L18.5 9.5",
  config: "M5 5h14v4H5zM5 15h14v4H5zM8 9v6M16 9v6",
  approvals: "M12 3 20 7v5c0 5-3.4 8.5-8 9-4.6-.5-8-4-8-9V7l8-4Zm-3 9 2 2 4-5",
  audit: "M7 4h10v16H7zM9.5 8h5M9.5 12h5M9.5 16h3",
  refresh: "M20 12a8 8 0 0 1-14.5 4.7M4 12A8 8 0 0 1 18.5 7.3M18.5 3v4h-4M5.5 21v-4h4",
  logout: "M10 6H6v12h4M13 8l4 4-4 4M8 12h9",
  language: "M4 5h9M8.5 3v2M6 5c.8 3.2 2.7 5.6 6 7M12 5c-.8 3.1-2.8 5.7-6.5 7.5M14 21l4-9 4 9M15.3 18h5.4",
  copy: "M8 8h10v12H8zM6 16H4V4h12v2",
  route: "M5 7a3 3 0 1 0 0 .1M19 17a3 3 0 1 0 0 .1M8 7h5a4 4 0 0 1 4 4v3",
  activity: "M4 12h4l2-6 4 12 2-6h4",
  check: "M5 12l4 4L19 6",
  x: "M6 6l12 12M18 6 6 18",
  add: "M12 5v14M5 12h14",
  save: "M5 5h12l2 2v12H5zM8 5v6h8M8 19v-5h8",
  upload: "M12 17V5M7 10l5-5 5 5M5 19h14"
} as const;

export type IconName = keyof typeof ICONS;

export function Icon({ name, className = "" }: { name: IconName; className?: string }) {
  return (
    <svg className={`icon ${className}`} viewBox="0 0 24 24" aria-hidden="true">
      <path d={ICONS[name]} />
    </svg>
  );
}

