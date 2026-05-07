"use client";

import { useState } from "react";

export function MarkApplied({ id, status }: { id: string; status: string }) {
  const [msg, setMsg] = useState<string | null>(null);
  async function go() {
    const r = await fetch(`/api/vacancies/${id}/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "Applied" }),
    });
    setMsg(r.ok ? "OK" : await r.text());
  }
  return (
    <div className="flex gap-2 items-center">
      <button
        type="button"
        onClick={go}
        className="px-3 py-1 bg-blue-600 rounded text-sm"
        disabled={status === "Applied"}
      >
        Mark Applied
      </button>
      {msg && <span className="text-xs">{msg}</span>}
    </div>
  );
}

export function GenerateFormal({ id }: { id: string }) {
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  async function go() {
    setBusy(true);
    setMsg(null);
    try {
      const r = await fetch(`/api/vacancies/${id}/generate/formal`, { method: "POST" });
      setMsg(r.ok ? "OK" : await r.text());
      if (r.ok) window.location.reload();
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="flex gap-2 items-center">
      <button
        type="button"
        onClick={go}
        className="px-3 py-1 bg-neutral-900 text-white rounded text-sm"
        disabled={busy}
      >
        Generate cover (formal)
      </button>
      {msg && <span className="text-xs">{msg}</span>}
    </div>
  );
}
