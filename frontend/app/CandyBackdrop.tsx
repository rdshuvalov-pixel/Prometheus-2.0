/** Статичный декоративный фон (карамельки), без анимаций и pointer-events. */

function CandyPiece({
  className,
  opacity,
}: {
  className?: string;
  opacity: number;
}) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 32 32"
      width={72}
      height={72}
      fill="none"
      aria-hidden
      style={{ opacity }}
    >
      <rect width="32" height="32" rx="6" fill="#fdebf3" stroke="#fbd5e5" strokeWidth="1" />
      <rect x="15" y="4" width="2" height="10" rx="1" fill="#ec8fb6" />
      <path
        d="M8 20c0-3.3 2.7-6 6-6h4c3.3 0 6 2.7 6 6v2H8v-2z"
        fill="#f6b7d1"
      />
      <ellipse cx="16" cy="16" rx="5" ry="3.5" fill="#fff7fa" opacity="0.95" />
      <path
        d="M12 15.5c1.2-1.2 2.8-1.5 4-1.5s2.8.3 4 1.5"
        stroke="#d96a99"
        strokeWidth="0.8"
        strokeLinecap="round"
      />
      <path
        d="M10 19c0-1.1.9-2 2-2h8c1.1 0 2 .9 2 2"
        stroke="#ec8fb6"
        strokeWidth="0.6"
        opacity="0.65"
      />
    </svg>
  );
}

export default function CandyBackdrop() {
  return (
    <div
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden"
      aria-hidden
    >
      <CandyPiece className="absolute left-[4%] top-[12%] rotate-[-12deg]" opacity={0.1} />
      <CandyPiece className="absolute left-[78%] top-[8%] rotate-[18deg]" opacity={0.08} />
      <CandyPiece className="absolute left-[62%] top-[48%] rotate-[33deg]" opacity={0.09} />
      <CandyPiece className="absolute left-[18%] top-[58%] rotate-[-22deg]" opacity={0.07} />
      <CandyPiece className="absolute left-[42%] top-[22%] rotate-[8deg]" opacity={0.06} />
      <CandyPiece className="absolute left-[88%] top-[72%] rotate-[-35deg]" opacity={0.11} />
      <CandyPiece className="absolute left-[8%] top-[82%] rotate-[25deg]" opacity={0.08} />
    </div>
  );
}
