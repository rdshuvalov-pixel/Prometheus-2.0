import type { ReactNode } from "react";

/** Декоративный фон: разные типы «конфет», без анимаций. Родитель задаёт z-index. */

type PaletteName =
  | "red"
  | "pink"
  | "yellow"
  | "orange"
  | "green"
  | "lime"
  | "blue"
  | "sky"
  | "purple";

const PALETTES: Record<
  PaletteName,
  { a: string; b: string; accent: string; highlight: string }
> = {
  red: { a: "#e11d48", b: "#ffffff", accent: "#be185d", highlight: "#fecdd3" },
  pink: { a: "#ec4899", b: "#fef08a", accent: "#db2777", highlight: "#fbcfe8" },
  yellow: { a: "#facc15", b: "#ffffff", accent: "#ca8a04", highlight: "#fef9c3" },
  orange: { a: "#f97316", b: "#ffffff", accent: "#c2410c", highlight: "#fed7aa" },
  green: { a: "#22c55e", b: "#ffffff", accent: "#15803d", highlight: "#bbf7d0" },
  lime: { a: "#84cc16", b: "#ffffff", accent: "#4d7c0f", highlight: "#ecfccb" },
  blue: { a: "#3b82f6", b: "#ffffff", accent: "#1d4ed8", highlight: "#bfdbfe" },
  sky: { a: "#38bdf8", b: "#ffffff", accent: "#0284c7", highlight: "#e0f2fe" },
  purple: { a: "#a855f7", b: "#fef08a", accent: "#7e22ce", highlight: "#e9d5ff" },
};

function LollipopSpiral({ palette }: { palette: PaletteName }) {
  const p = PALETTES[palette];
  return (
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" aria-hidden>
      <rect x="46" y="58" width="8" height="38" rx="3" fill="#94a3b8" />
      <circle cx="50" cy="38" r="28" fill={p.a} stroke={p.accent} strokeWidth="2" />
      <path
        d="M50 18 A20 20 0 0 1 50 58 A16 16 0 0 0 50 26 A12 12 0 0 1 50 50 A8 8 0 0 0 50 34"
        fill="none"
        stroke={p.b}
        strokeWidth="4"
        strokeLinecap="round"
      />
      <path
        d="M50 22 A18 18 0 0 0 50 54 A14 14 0 0 1 50 30"
        fill="none"
        stroke={p.highlight}
        strokeWidth="2"
        opacity="0.9"
      />
    </svg>
  );
}

function WrappedCandy({ palette }: { palette: PaletteName }) {
  const p = PALETTES[palette];
  return (
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" aria-hidden>
      <path
        d="M8 50 L18 42 L22 58 L14 56 Z"
        fill={p.a}
        stroke={p.accent}
        strokeWidth="1.5"
      />
      <path
        d="M92 50 L82 42 L78 58 L86 56 Z"
        fill={p.a}
        stroke={p.accent}
        strokeWidth="1.5"
      />
      <ellipse cx="50" cy="50" rx="34" ry="22" fill={p.a} stroke={p.accent} strokeWidth="2" />
      <ellipse cx="42" cy="44" rx="12" ry="8" fill={p.highlight} opacity="0.55" />
    </svg>
  );
}

function SugarDragee({ colors }: { colors: [PaletteName, PaletteName, PaletteName] }) {
  const dots: { cx: number; cy: number; r: number; pal: PaletteName }[] = [
    { cx: 22, cy: 55, r: 14, pal: colors[0] },
    { cx: 50, cy: 48, r: 16, pal: colors[1] },
    { cx: 78, cy: 58, r: 13, pal: colors[2] },
  ];
  return (
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" aria-hidden>
      {dots.map((d) => {
        const pl = PALETTES[d.pal];
        return (
          <g key={`${d.cx}-${d.cy}`}>
            <circle cx={d.cx} cy={d.cy} r={d.r} fill={pl.a} stroke={pl.accent} strokeWidth="1.5" />
            <ellipse
              cx={d.cx - d.r * 0.35}
              cy={d.cy - d.r * 0.35}
              rx={d.r * 0.35}
              ry={d.r * 0.22}
              fill={pl.highlight}
              opacity="0.65"
            />
          </g>
        );
      })}
    </svg>
  );
}

function Marshmallow({ palette }: { palette: PaletteName }) {
  const p = PALETTES[palette];
  return (
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" aria-hidden>
      <rect x="14" y="28" width="72" height="44" rx="22" fill="#ffffff" stroke="#e2e8f0" strokeWidth="2" />
      <rect x="14" y="38" width="72" height="12" fill={p.a} opacity="0.55" />
      <rect x="14" y="52" width="72" height="10" fill={p.accent} opacity="0.35" />
      <ellipse cx="38" cy="36" rx="14" ry="8" fill="#ffffff" opacity="0.75" />
    </svg>
  );
}

function JellySlice({ palette }: { palette: PaletteName }) {
  const p = PALETTES[palette];
  return (
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" aria-hidden>
      <path d="M10 85 Q50 15 90 85 Z" fill={p.a} stroke={p.accent} strokeWidth="2" />
      {[0, 1, 2, 3, 4].map((i) => (
        <line
          key={i}
          x1="50"
          y1="72"
          x2={50 + (i - 2) * 10}
          y2="38"
          stroke={p.b}
          strokeWidth="2"
          opacity="0.75"
        />
      ))}
      <rect x="12" y="82" width="76" height="6" rx="2" fill="#ffffff" opacity="0.85" strokeDasharray="4 3" />
    </svg>
  );
}

type Item =
  | { kind: "lollipop"; top: string; left: string; rot: number; scale: number; op: number; palette: PaletteName }
  | { kind: "wrapped"; top: string; left: string; rot: number; scale: number; op: number; palette: PaletteName }
  | { kind: "dragee"; top: string; left: string; rot: number; scale: number; op: number; colors: [PaletteName, PaletteName, PaletteName] }
  | { kind: "marshmallow"; top: string; left: string; rot: number; scale: number; op: number; palette: PaletteName }
  | { kind: "jelly"; top: string; left: string; rot: number; scale: number; op: number; palette: PaletteName };

const ITEMS: Item[] = [
  { kind: "lollipop", top: "6%", left: "4%", rot: -14, scale: 1.05, op: 0.48, palette: "red" },
  { kind: "wrapped", top: "11%", left: "72%", rot: 18, scale: 0.92, op: 0.44, palette: "yellow" },
  { kind: "jelly", top: "26%", left: "31%", rot: 8, scale: 1.0, op: 0.42, palette: "orange" },
  { kind: "marshmallow", top: "42%", left: "83%", rot: -22, scale: 0.98, op: 0.4, palette: "pink" },
  {
    kind: "dragee",
    top: "51%",
    left: "16%",
    rot: 0,
    scale: 1.0,
    op: 0.5,
    colors: ["blue", "green", "purple"],
  },
  { kind: "lollipop", top: "58%", left: "48%", rot: 24, scale: 1.12, op: 0.46, palette: "sky" },
  { kind: "wrapped", top: "8%", left: "42%", rot: -8, scale: 1.08, op: 0.43, palette: "green" },
  { kind: "jelly", top: "72%", left: "8%", rot: -18, scale: 0.95, op: 0.41, palette: "lime" },
  { kind: "marshmallow", top: "18%", left: "88%", rot: 12, scale: 0.88, op: 0.38, palette: "purple" },
  {
    kind: "dragee",
    top: "34%",
    left: "58%",
    rot: -6,
    scale: 0.9,
    op: 0.47,
    colors: ["red", "yellow", "orange"],
  },
  { kind: "lollipop", top: "78%", left: "62%", rot: -28, scale: 1.0, op: 0.45, palette: "pink" },
  { kind: "wrapped", top: "64%", left: "28%", rot: 15, scale: 1.05, op: 0.42, palette: "blue" },
  { kind: "jelly", top: "14%", left: "18%", rot: -10, scale: 1.0, op: 0.44, palette: "green" },
  { kind: "marshmallow", top: "88%", left: "44%", rot: 6, scale: 0.92, op: 0.39, palette: "yellow" },
  {
    kind: "dragee",
    top: "22%",
    left: "52%",
    rot: 20,
    scale: 0.85,
    op: 0.46,
    colors: ["sky", "pink", "lime"],
  },
  { kind: "lollipop", top: "46%", left: "6%", rot: 10, scale: 0.98, op: 0.43, palette: "purple" },
  { kind: "wrapped", top: "82%", left: "76%", rot: -12, scale: 1.1, op: 0.41, palette: "orange" },
  { kind: "jelly", top: "36%", left: "92%", rot: 32, scale: 0.88, op: 0.4, palette: "red" },
];

export default function CandyBackdrop() {
  const base = 96;
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
      {ITEMS.map((it, i) => {
        const px = Math.round(base * it.scale);
        const style = {
          top: it.top,
          left: it.left,
          width: px,
          height: px,
          opacity: it.op,
          transform: `rotate(${it.rot}deg)`,
        } as const;
        let node: ReactNode;
        switch (it.kind) {
          case "lollipop":
            node = <LollipopSpiral palette={it.palette} />;
            break;
          case "wrapped":
            node = <WrappedCandy palette={it.palette} />;
            break;
          case "dragee":
            node = <SugarDragee colors={it.colors} />;
            break;
          case "marshmallow":
            node = <Marshmallow palette={it.palette} />;
            break;
          case "jelly":
            node = <JellySlice palette={it.palette} />;
            break;
        }
        return (
          <div key={i} className="absolute" style={style}>
            {node}
          </div>
        );
      })}
    </div>
  );
}
