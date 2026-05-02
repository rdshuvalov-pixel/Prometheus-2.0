"use client";

import { useState } from "react";

export function CopyFormal({ body }: { body: string | null }) {
  const [label, setLabel] = useState("Копировать сопроводительное");
  const disabled = !body;

  async function onClick() {
    if (!body) return;
    try {
      await navigator.clipboard.writeText(body);
      setLabel("Скопировано");
      setTimeout(() => setLabel("Копировать сопроводительное"), 1500);
    } catch {
      setLabel("Ошибка копирования");
      setTimeout(() => setLabel("Копировать сопроводительное"), 2000);
    }
  }

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      title={disabled ? "Нет formal письма (запустите run_write)" : undefined}
      className="px-3 py-1.5 text-sm rounded border border-slate-600 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed"
    >
      {disabled ? "Нет formal письма" : label}
    </button>
  );
}
