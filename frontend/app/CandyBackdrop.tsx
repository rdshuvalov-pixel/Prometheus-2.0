/** Декоративный фон: родитель задаёт z-index поверх градиента; без анимаций. */

function CandyPiece({
  className,
  opacity,
  scale = 1,
}: {
  className?: string;
  opacity: number;
  scale?: number;
}) {
  const size = Math.round(96 * scale);
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 32 32"
      width={size}
      height={size}
      aria-hidden
      style={{ opacity }}
    >
      <rect width="32" height="32" rx="6" fill="#fce7f3" stroke="#f472b6" strokeWidth="1.2" />
      <rect x="15" y="4" width="2" height="10" rx="1" fill="#db2777" />
      <path d="M8 20c0-3.3 2.7-6 6-6h4c3.3 0 6 2.7 6 6v2H8v-2z" fill="#fbcfe8" />
      <ellipse cx="16" cy="16" rx="5" ry="3.5" fill="#fff1f2" />
      <path
        d="M12 15.5c1.2-1.2 2.8-1.5 4-1.5s2.8.3 4 1.5"
        stroke="#be185d"
        strokeWidth="1"
        strokeLinecap="round"
        fill="none"
      />
      <path
        d="M10 19c0-1.1.9-2 2-2h8c1.1 0 2 .9 2 2"
        stroke="#db2777"
        strokeWidth="0.7"
        fill="none"
        opacity="0.75"
      />
    </svg>
  );
}

export default function CandyBackdrop() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
      <CandyPiece className="absolute left-[3%] top-[10%] -rotate-12" opacity={0.38} scale={1.15} />
      <CandyPiece className="absolute left-[72%] top-[6%] rotate-[20deg]" opacity={0.34} scale={0.95} />
      <CandyPiece className="absolute left-[58%] top-[42%] rotate-[32deg]" opacity={0.36} />
      <CandyPiece className="absolute left-[15%] top-[52%] -rotate-[18deg]" opacity={0.32} scale={1.05} />
      <CandyPiece className="absolute left-[38%] top-[18%] rotate-[10deg]" opacity={0.4} scale={1.2} />
      <CandyPiece className="absolute left-[84%] top-[68%] -rotate-[28deg]" opacity={0.35} />
      <CandyPiece className="absolute left-[6%] top-[78%] rotate-[22deg]" opacity={0.33} scale={0.9} />
      <CandyPiece className="absolute left-[48%] top-[62%] -rotate-6" opacity={0.37} scale={1.1} />
      <CandyPiece className="absolute left-[92%] top-[28%] rotate-[40deg]" opacity={0.3} scale={0.85} />
      <CandyPiece className="absolute left-[28%] top-[88%] rotate-12" opacity={0.31} />
    </div>
  );
}
