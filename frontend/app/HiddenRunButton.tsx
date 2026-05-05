"use client";

import { useCallback, useMemo, useState } from "react";

type ToastState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "ok"; message: string }
  | { kind: "err"; message: string };

function normalizeErrorMessage(x: unknown): string {
  if (!x) return "Unknown error";
  if (typeof x === "string") return x;
  if (x instanceof Error) return x.message || "Error";
  try {
    return JSON.stringify(x);
  } catch {
    return "Error";
  }
}

export default function HiddenRunButton() {
  const [state, setState] = useState<ToastState>({ kind: "idle" });

  const busy = state.kind === "loading";
  const toast = useMemo(() => {
    if (state.kind === "ok") return { tone: "ok" as const, text: state.message };
    if (state.kind === "err") return { tone: "err" as const, text: state.message };
    if (state.kind === "loading") return { tone: "info" as const, text: "Queuing pipeline…" };
    return null;
  }, [state]);

  const run = useCallback(async () => {
    if (busy) return;
    setState({ kind: "loading" });
    try {
      const r = await fetch("/api/pipeline/run", { method: "POST" });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) {
        const msg = typeof data?.error === "string" ? data.error : `HTTP ${r.status}`;
        throw new Error(msg);
      }
      const msg = typeof data?.status === "string" ? data.status : "queued";
      setState({ kind: "ok", message: msg === "queued" ? "Pipeline queued" : `Pipeline: ${msg}` });
    } catch (e) {
      setState({ kind: "err", message: normalizeErrorMessage(e) });
    } finally {
      window.setTimeout(() => setState({ kind: "idle" }), 4000);
    }
  }, [busy]);

  // Positioned to match yellow wrapped candy in CandyBackdrop.tsx (top 11%, left 72%, scale 0.92).
  return (
    <>
      <button
        type="button"
        aria-label="Run full pipeline"
        onClick={run}
        className="fixed z-[2] bg-transparent border-0 cursor-pointer"
        style={{
          top: "11%",
          left: "72%",
          width: Math.round(96 * 0.92),
          height: Math.round(96 * 0.92),
          pointerEvents: "auto",
        }}
      />
      {toast ? (
        <div
          className={[
            "fixed z-[50] right-4 top-4 max-w-[420px] rounded-xl border px-4 py-3 text-sm shadow-lg backdrop-blur",
            toast.tone === "ok"
              ? "bg-emerald-50/95 border-emerald-200 text-emerald-900"
              : toast.tone === "err"
                ? "bg-rose-50/95 border-rose-200 text-rose-900"
                : "bg-white/90 border-neutral-200 text-neutral-900",
          ].join(" ")}
          role="status"
        >
          {toast.text}
        </div>
      ) : null}
    </>
  );
}

