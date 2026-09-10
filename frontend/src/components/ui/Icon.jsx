// Inline SVG icon set — the stack doc rules out a component/icon library,
// and these keep the bundle at zero extra dependencies. All icons share a
// 24px grid and inherit `currentColor`.

const PATHS = {
  search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></>,
  plus: <><path d="M12 5v14M5 12h14" /></>,
  check: <path d="m4 12 5 5L20 6" />,
  sparkles: (
    <>
      <path d="M12 3l1.6 4.4L18 9l-4.4 1.6L12 15l-1.6-4.4L6 9l4.4-1.6L12 3Z" />
      <path d="M18.5 15.5l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8.8-2.2Z" />
    </>
  ),
  users: (
    <>
      <path d="M16 19v-1.5a3.5 3.5 0 0 0-3.5-3.5h-5A3.5 3.5 0 0 0 4 17.5V19" />
      <circle cx="10" cy="7.5" r="3.5" />
      <path d="M20 19v-1.5a3.5 3.5 0 0 0-2.6-3.4M15.5 4.2a3.5 3.5 0 0 1 0 6.6" />
    </>
  ),
  pin: (
    <>
      <path d="M12 21s7-5.6 7-11a7 7 0 1 0-14 0c0 5.4 7 11 7 11Z" />
      <circle cx="12" cy="10" r="2.5" />
    </>
  ),
  tag: (
    <>
      <path d="M3 12.5V4h8.5L21 13.5 13.5 21 3 12.5Z" />
      <circle cx="7.5" cy="8" r="1.4" />
    </>
  ),
  building: (
    <>
      <path d="M4 21V5.5A1.5 1.5 0 0 1 5.5 4h7A1.5 1.5 0 0 1 14 5.5V21" />
      <path d="M14 10h4.5A1.5 1.5 0 0 1 20 11.5V21M3 21h18" />
      <path d="M7.5 8h3M7.5 12h3M7.5 16h3M17 14h0M17 18h0" />
    </>
  ),
  pencil: (
    <>
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
    </>
  ),
  image: (
    <>
      <rect x="3" y="4" width="18" height="16" rx="2" />
      <circle cx="8.5" cy="9.5" r="1.5" />
      <path d="m21 15-5-5L5 21" />
    </>
  ),
  door: (
    <>
      <path d="M6 21V4.5A1.5 1.5 0 0 1 7.5 3h9A1.5 1.5 0 0 1 18 4.5V21M4 21h16" />
      <circle cx="14.5" cy="12.5" r="1" />
    </>
  ),
  calendar: (
    <>
      <rect x="3.5" y="5" width="17" height="15.5" rx="2" />
      <path d="M3.5 10h17M8 3v4M16 3v4" />
    </>
  ),
  mail: (
    <>
      <rect x="3" y="5.5" width="18" height="13" rx="2" />
      <path d="m3.5 7 8.5 6 8.5-6" />
    </>
  ),
  inbox: (
    <>
      <path d="M3.5 13.5h4l1.5 3h6l1.5-3h4" />
      <path d="M4.6 5.9 3.5 13.5v3.6a2 2 0 0 0 2 2h13a2 2 0 0 0 2-2v-3.6L19.4 5.9A2 2 0 0 0 17.5 4.5h-11a2 2 0 0 0-1.9 1.4Z" />
    </>
  ),
  alert: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7.5v5.5M12 16.3h.01" />
    </>
  ),
  sun: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.2 5.2l1.4 1.4M17.4 17.4l1.4 1.4M18.8 5.2l-1.4 1.4M6.6 17.4l-1.4 1.4" />
    </>
  ),
  moon: <path d="M20 14.2A8.2 8.2 0 0 1 9.8 4 8.5 8.5 0 1 0 20 14.2Z" />,
  arrowLeft: <><path d="M19 12H5M11 6l-6 6 6 6" /></>,
  arrowRight: <><path d="M5 12h14M13 6l6 6-6 6" /></>,
  logout: (
    <>
      <path d="M9 21H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3" />
      <path d="M16 17l5-5-5-5M21 12H9" />
    </>
  ),
  x: <path d="M6 6l12 12M18 6 6 18" />,
  sliders: (
    <>
      <path d="M4 7h9M17 7h3M4 17h3M11 17h9" />
      <circle cx="15" cy="7" r="2" />
      <circle cx="9" cy="17" r="2" />
    </>
  ),
  // Amenity icons
  wifi: (
    <>
      <path d="M2.5 9a15 15 0 0 1 19 0M5.5 12.5a10.5 10.5 0 0 1 13 0M8.5 16a6 6 0 0 1 7 0" />
      <path d="M12 19.5h.01" />
    </>
  ),
  car: (
    <>
      <path d="M4 16.5V19a1 1 0 0 0 1 1h1.5a1 1 0 0 0 1-1v-1.5M16.5 17.5V19a1 1 0 0 0 1 1H19a1 1 0 0 0 1-1v-2.5" />
      <path d="M3.5 16.5h17V12l-1.8-4.6A2 2 0 0 0 16.8 6H7.2a2 2 0 0 0-1.9 1.4L3.5 12v4.5Z" />
      <path d="M3.5 12h17M7 14.2h.01M17 14.2h.01" />
    </>
  ),
  board: (
    <>
      <rect x="3" y="4" width="18" height="12.5" rx="1.5" />
      <path d="M12 16.5V21M8.5 8.5h7M8.5 12h4" />
    </>
  ),
  projector: (
    <>
      <rect x="2.5" y="8" width="19" height="9.5" rx="2" />
      <circle cx="9" cy="12.75" r="2.75" />
      <path d="M17 11.5h1.5M5.5 19.5v1M18.5 19.5v1" />
    </>
  ),
  kitchen: (
    <>
      <path d="M6 3v7a2.5 2.5 0 0 0 5 0V3M8.5 12.5V21" />
      <path d="M17 3c-1.5 1.2-2 3-2 5.5s.7 3.5 2 3.5V21" />
    </>
  ),
  ac: (
    <>
      <rect x="3" y="4.5" width="18" height="7" rx="2" />
      <path d="M7 15.5c0 1.5-1 2-1 3.5M12 15.5c0 1.5-1 2-1 3.5M17 15.5c0 1.5-1 2-1 3.5" />
      <path d="M6.5 8h11" />
    </>
  ),
}

export default function Icon({ name, size = 18, strokeWidth = 1.6, ...rest }) {
  const path = PATHS[name]
  if (!path) return null
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      {...rest}
    >
      {path}
    </svg>
  )
}
