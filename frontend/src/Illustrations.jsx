import React from "react";

// Original inline vector art in the app's own palette (tailwind.config.js).
const C = {
  paper: "#f2f4ee",
  sheet: "#ffffff",
  bar: "#e5eee1",
  ink: "#161a16",
  muted: "#5b655c",
  rule: "#ccd6c8",
  stamp: "#1c3faa",
  good: "#1e6b3d",
  mid: "#8a6412",
  low: "#a4352a",
};

const Svg = ({ viewBox, title, className, children }) => (
  <svg viewBox={viewBox} className={className} role="img" aria-label={title} preserveAspectRatio="xMidYMid slice">
    <title>{title}</title>
    {children}
  </svg>
);

/* A resume page: header block, avatar, text lines. */
const Resume = ({ x, y, w = 180, h = 240, highlight }) => {
  const line = (dy, lw, color = C.rule) => (
    <rect x={x + 20} y={y + dy} width={lw} height="7" rx="3.5" fill={color} />
  );
  return (
    <g>
      <rect x={x + 6} y={y + 8} width={w} height={h} rx="12" fill={C.ink} opacity=".12" />
      <rect x={x} y={y} width={w} height={h} rx="12" fill={C.sheet} />
      <circle cx={x + 36} cy={y + 38} r="16" fill={C.bar} />
      <circle cx={x + 36} cy={y + 33} r="6" fill={C.muted} opacity=".5" />
      <path d={`M${x + 25} ${y + 48}a11 9 0 0 1 22 0z`} fill={C.muted} opacity=".5" />
      <rect x={x + 62} y={y + 28} width={w * 0.45} height="9" rx="4.5" fill={C.ink} />
      <rect x={x + 62} y={y + 43} width={w * 0.3} height="6" rx="3" fill={C.rule} />
      {line(78, w * 0.3, C.stamp)}
      {line(94, w - 40)}
      {line(108, w - 60)}
      {highlight && <rect x={x + 12} y={y + 117} width={w - 24} height="21" rx="6" fill={C.stamp} opacity=".12" />}
      {line(123, w - 50, highlight ? C.stamp : C.rule)}
      {line(152, w * 0.3, C.stamp)}
      {line(168, w - 45)}
      {line(182, w - 70)}
      {line(196, w - 55)}
      {h > 220 && line(210, w - 80)}
    </g>
  );
};

const Chip = ({ x, y, w, label, color = C.good }) => (
  <g>
    <rect x={x} y={y} width={w} height="26" rx="13" fill={C.sheet} stroke={C.rule} />
    <circle cx={x + 14} cy={y + 13} r="4" fill={color} />
    <text x={x + 24} y={y + 17.5} fontFamily="Archivo, sans-serif" fontSize="12" fontWeight="600" fill={C.ink}>
      {label}
    </text>
  </g>
);

export const AuthArt = ({ className }) => (
  <Svg viewBox="0 0 600 760" title="A resume being scanned, with a score and skill tags" className={className}>
    <rect width="600" height="760" fill={C.ink} />
    <g opacity=".08" stroke={C.paper}>
      {Array.from({ length: 16 }, (_, i) => (
        <path key={i} d={`M0 ${i * 50}H600`} />
      ))}
      {Array.from({ length: 13 }, (_, i) => (
        <path key={i} d={`M${i * 50} 0V760`} />
      ))}
    </g>
    <circle cx="300" cy="250" r="190" fill={C.stamp} opacity=".35" />

    <g transform="rotate(-6 300 250)">
      <Resume x={185} y={90} w={230} h={300} highlight />
    </g>

    {/* magnifier */}
    <g transform="translate(380 230)">
      <circle r="52" fill={C.sheet} opacity=".18" stroke={C.paper} strokeWidth="10" />
      <path d="M38 38l48 48" stroke={C.paper} strokeWidth="16" strokeLinecap="round" />
    </g>

    {/* score card */}
    <g transform="translate(70 300)">
      <rect width="150" height="96" rx="14" fill={C.sheet} />
      <text x="18" y="30" fontFamily="IBM Plex Mono, monospace" fontSize="10" letterSpacing="1.5" fill={C.muted}>SCORE</text>
      <text x="18" y="70" fontFamily="IBM Plex Mono, monospace" fontSize="38" fontWeight="500" fill={C.ink}>82</text>
      <g transform="translate(78 50)">
        {Array.from({ length: 5 }, (_, i) => (
          <rect key={i} x={i * 11} y="0" width="8" height="20" rx="2" fill={i < 4 ? C.good : C.bar} />
        ))}
      </g>
    </g>

    <Chip x={430} y={80} w={86} label="Python" />
    <Chip x={450} y={116} w={78} label="React" color={C.stamp} />
    <Chip x={402} y={342} w={104} label="SQL · +2" color={C.mid} />
  </Svg>
);

export const UploadArt = ({ className }) => (
  <Svg viewBox="0 0 320 200" title="A resume being uploaded" className={className}>
    <rect width="320" height="200" fill={C.bar} />
    <circle cx="250" cy="40" r="60" fill={C.stamp} opacity=".08" />
    <g transform="scale(.62) translate(120 50)">
      <Resume x={0} y={0} w={170} h={230} />
    </g>
    <g transform="translate(210 70)">
      <rect width="80" height="80" rx="18" fill={C.stamp} />
      <path d="M40 58V24M26 37l14-14 14 14" fill="none" stroke={C.sheet} strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" />
    </g>
    <path d="M190 110h14" stroke={C.stamp} strokeWidth="3" strokeDasharray="3 5" strokeLinecap="round" />
  </Svg>
);

export const AnalyzeArt = ({ className }) => (
  <Svg viewBox="0 0 320 200" title="Skills being extracted from a resume" className={className}>
    <rect width="320" height="200" fill={C.bar} />
    <g transform="scale(.62) translate(60 50)">
      <Resume x={0} y={0} w={170} h={230} highlight />
    </g>
    {/* scan line */}
    <rect x="30" y="112" width="120" height="3" rx="1.5" fill={C.stamp} />
    <path d="M150 113C180 113 180 60 200 60M150 113h50M150 113C180 113 180 166 200 166" fill="none" stroke={C.stamp} strokeWidth="2" strokeDasharray="4 4" />
    <Chip x={200} y={47} w={96} label="Django" />
    <Chip x={200} y={100} w={96} label="Docker" color={C.stamp} />
    <Chip x={200} y={153} w={96} label="Figma" color={C.mid} />
  </Svg>
);

export const MatchArt = ({ className }) => (
  <Svg viewBox="0 0 320 200" title="Ranked job matches with scores" className={className}>
    <rect width="320" height="200" fill={C.bar} />
    {[
      [30, 88, C.good, true],
      [58, 72, C.mid, false],
      [86, 61, C.muted, false],
    ].map(([y, pct, color, top], i) => (
      <g key={i} transform={`translate(${40 + i * 8} ${y + i * 20})`} opacity={1 - i * 0.2}>
        <rect width="230" height="52" rx="12" fill={C.sheet} stroke={top ? C.good : C.rule} strokeWidth={top ? 2 : 1} />
        <rect x="14" y="14" width="24" height="24" rx="6" fill={color} opacity=".15" />
        <path d="M20 26h12M26 20v12" stroke={color} strokeWidth="3" strokeLinecap="round" opacity={top ? 0 : 1} />
        {top && <path d="M19 26l5 5 9-10" fill="none" stroke={C.good} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />}
        <rect x="50" y="16" width="90" height="8" rx="4" fill={C.ink} />
        <rect x="50" y="30" width="60" height="6" rx="3" fill={C.rule} />
        <text x="214" y="32" textAnchor="end" fontFamily="IBM Plex Mono, monospace" fontSize="14" fontWeight="600" fill={color}>
          {pct}%
        </text>
      </g>
    ))}
  </Svg>
);

export const InterviewArt = ({ className }) => (
  <Svg viewBox="0 0 520 320" title="Two people talking across a table" className={className}>
    <rect width="520" height="320" fill={C.ink} />
    <circle cx="260" cy="140" r="130" fill={C.stamp} opacity=".35" />
    {/* speech bubbles */}
    <g transform="translate(130 40)">
      <rect width="110" height="46" rx="14" fill={C.sheet} />
      <path d="M26 46l-6 14 18-14z" fill={C.sheet} />
      <rect x="16" y="15" width="70" height="7" rx="3.5" fill={C.rule} />
      <rect x="16" y="27" width="46" height="7" rx="3.5" fill={C.stamp} />
    </g>
    <g transform="translate(290 70)">
      <rect width="100" height="40" rx="14" fill={C.good} />
      <path d="M74 40l6 12-16-12z" fill={C.good} />
      <path d="M38 20l8 8 16-16" fill="none" stroke={C.sheet} strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" />
    </g>
    {/* left person */}
    <circle cx="150" cy="150" r="28" fill="#e8b98f" />
    <path d="M122 146a28 28 0 0 1 56 -6c-10-10-40-12-56 6z" fill={C.ink} />
    <path d="M100 250c0-50 22-70 50-70s50 20 50 70z" fill={C.mid} />
    {/* right person */}
    <circle cx="370" cy="150" r="28" fill="#9c6b48" />
    <path d="M340 150c-2-30 22-40 38-34 16 4 24 18 20 34-6-12-22-20-58 0z" fill="#2b2320" />
    <path d="M320 250c0-50 22-70 50-70s50 20 50 70z" fill={C.stamp} />
    {/* table */}
    <rect x="60" y="240" width="400" height="16" rx="8" fill={C.paper} />
    <rect x="95" y="256" width="12" height="64" fill={C.rule} />
    <rect x="413" y="256" width="12" height="64" fill={C.rule} />
    <g transform="translate(215 214) rotate(-4)">
      <rect width="80" height="30" rx="4" fill={C.sheet} />
      <rect x="10" y="8" width="44" height="5" rx="2.5" fill={C.rule} />
      <rect x="10" y="18" width="30" height="5" rx="2.5" fill={C.stamp} />
    </g>
  </Svg>
);
