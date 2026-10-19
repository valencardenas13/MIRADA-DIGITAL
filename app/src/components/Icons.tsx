const base = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
  viewBox: '0 0 24 24',
  'aria-hidden': true,
};

export const IconInstagram = () => (
  <svg {...base}>
    <rect x="3" y="3" width="18" height="18" rx="5" />
    <circle cx="12" cy="12" r="4" />
    <circle cx="17.5" cy="6.5" r="0.6" fill="currentColor" />
  </svg>
);

export const IconWhatsApp = () => (
  <svg {...base}>
    <path d="M20.5 11.6a8.5 8.5 0 0 1-12.6 7.4L3.5 20.5l1.5-4.3a8.5 8.5 0 1 1 15.5-4.6z" />
    <path d="M9 9.5c.3 1.7 1.8 3.7 3.8 4.5l1.2-1 1.8.8c-.2 1.1-1.1 1.7-2 1.6-2.8-.4-5.6-3.2-6-6 0-.9.5-1.8 1.6-2l.8 1.8-1.2.3z" />
  </svg>
);

export const IconSearch = () => (
  <svg {...base}>
    <circle cx="11" cy="11" r="7" />
    <path d="m20 20-3.5-3.5" />
  </svg>
);

export const IconMeta = () => (
  <svg {...base}>
    <path d="M3 15c0-4 2.2-8 4.8-8 3.4 0 5.6 10 8.6 10C18.6 17 21 15 21 12s-1.6-5-3.6-5c-3 0-5.6 10-9.4 10C5 17 3 16.4 3 15z" />
  </svg>
);

export const IconEye = () => (
  <svg {...base}>
    <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);

export const IconChart = () => (
  <svg {...base}>
    <path d="M3 3v18h18" />
    <path d="m7 15 4-4 3 3 6-6" />
  </svg>
);

export const IconSwap = () => (
  <svg {...base}>
    <path d="M7 4 3 8l4 4" />
    <path d="M3 8h14" />
    <path d="m17 20 4-4-4-4" />
    <path d="M21 16H7" />
  </svg>
);

export const IconRocket = () => (
  <svg {...base}>
    <path d="M5 15c-1.5 1.3-2 5-2 5s3.7-.5 5-2c.7-.8.7-2.1-.1-2.9-.8-.8-2.1-.8-2.9-.1z" />
    <path d="m12 15-3-3a22 22 0 0 1 2-4A12.9 12.9 0 0 1 22 2c0 2.7-.8 7.5-6 11a22 22 0 0 1-4 2z" />
  </svg>
);

export const IconQuestion = () => (
  <svg {...base}>
    <circle cx="12" cy="12" r="9.5" />
    <path d="M9.2 9a3 3 0 0 1 5.8 1c0 2-3 2.5-3 4.5" />
    <circle cx="12" cy="17.6" r="0.6" fill="currentColor" />
  </svg>
);

export const IconCheck = () => (
  <svg {...base}>
    <path d="m5 12.5 4.5 4.5L19 7.5" />
  </svg>
);

export const IconX = () => (
  <svg {...base}>
    <path d="M6 6l12 12M18 6 6 18" />
  </svg>
);

export const IconArrow = () => (
  <svg {...base}>
    <path d="M5 12h14M13 6l6 6-6 6" />
  </svg>
);

export const IconPlus = () => (
  <svg {...base}>
    <path d="M12 5v14M5 12h14" />
  </svg>
);
