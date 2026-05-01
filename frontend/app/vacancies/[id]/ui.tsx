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
