"use client";

import { useState } from "react";

type Step = "crawl" | "normalize" | "dedup" | "score" | "promote" | "report";

const STEPS: { id: Step; label: string }[] = [
  { id: "crawl", label: "Run crawl → stage" },
  { id: "normalize", label: "Run normalize" },
  { id: "dedup", label: "Run dedup" },
  { id: "score", label: "Run score + filters" },
  { id: "promote", label: "Promote to vacancies" },
  { id: "report", label: "Run report" },
];

export function StepButtons() {
  const [busy, setBusy] = useState<Step | null>(null);
  const [last, setLast] = useState<{ step: Step; ok: boolean; message: string } | null>(null);

  async function run(step: Step) {
    setBusy(step);
    setLast(null);
    try {
      const res = await fetch(`/api/pipeline/step/${step}`, { method: "POST" });
      const text = await res.text();
      setLast({ step, ok: res.ok, message: text });
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setLast({ step, ok: false, message: msg });
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="rounded-lg border border-neutral-200 bg-white/90 shadow-sm p-4 space-y-3">
      <div className="flex items-baseline justify-between gap-2">
        <h2 className="text-lg font-medium text-neutral-900">Run steps</h2>
        {busy ? <span className="text-xs text-neutral-600">Running: {busy}…</span> : null}
      </div>
      <div className="flex flex-wrap gap-2">
        {STEPS.map((s) => (
          <button
            key={s.id}
            type="button"
            disabled={busy !== null}
            onClick={() => run(s.id)}
            className="text-xs px-3 py-1.5 rounded border border-neutral-300 bg-neutral-50 text-neutral-900 hover:bg-neutral-100 disabled:opacity-60"
          >
            {s.label}
          </button>
        ))}
      </div>
      {last ? (
        <pre
          className={
            "whitespace-pre-wrap break-words rounded border p-2 text-[11px] " +
            (last.ok ? "border-emerald-200 bg-emerald-50 text-emerald-900" : "border-red-200 bg-red-50 text-red-900")
          }
        >
          {last.message}
        </pre>
      ) : null}
    </div>
  );
}

