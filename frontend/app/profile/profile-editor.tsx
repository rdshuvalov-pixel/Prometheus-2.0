"use client";

import { useState } from "react";
import MDEditor from "@uiw/react-md-editor";
import "@uiw/react-md-editor/markdown-editor.css";

export default function ProfileEditor({
  profile,
}: {
  profile: Record<string, unknown>;
}) {
  const [profession, setProfession] = useState(String(profile.profession || ""));
  const [keywords, setKeywords] = useState((profile.search_keywords as string[])?.join(", ") || "");
  const [resume, setResume] = useState(String(profile.resume_md || ""));
  const [interview, setInterview] = useState(String(profile.interview_md || ""));
  const [workHistory, setWorkHistory] = useState(String(profile.work_history_md || ""));
  const [weights, setWeights] = useState(JSON.stringify(profile.scoring_overrides || {}, null, 2));
  const [msg, setMsg] = useState<string | null>(null);
  const [preview, setPreview] = useState<string | null>(null);

  async function save() {
    let overrides: unknown = null;
    try {
      overrides = weights.trim() ? JSON.parse(weights) : null;
    } catch {
      setMsg("Неверный JSON в scoring_overrides");
      return;
    }
    const r = await fetch("/api/profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id: profile.id,
        profession,
        search_keywords: keywords.split(",").map((s) => s.trim()).filter(Boolean),
        resume_md: resume,
        interview_md: interview,
        work_history_md: workHistory,
        scoring_overrides: overrides,
      }),
    });
    setMsg(r.ok ? "Сохранено" : await r.text());
  }

  async function previewWeights() {
    let overrides: unknown = null;
    try {
      overrides = weights.trim() ? JSON.parse(weights) : null;
    } catch {
      setPreview("Неверный JSON в scoring_overrides");
      return;
    }
    const r = await fetch("/api/scoring/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scoring_overrides: overrides }),
    });
    const data = await r.json();
    setPreview(JSON.stringify(data, null, 2));
  }

  return (
    <div className="space-y-4" data-color-mode="dark">
      <label className="block">
        <span className="text-sm text-slate-400">Профессия</span>
        <input
          className="w-full bg-slate-900 border border-slate-700 rounded p-2 mt-1"
          value={profession}
          onChange={(e) => setProfession(e.target.value)}
        />
      </label>
      <label className="block">
        <span className="text-sm text-slate-400">Ключевые слова (через запятую)</span>
        <input
          className="w-full bg-slate-900 border border-slate-700 rounded p-2 mt-1"
          value={keywords}
          onChange={(e) => setKeywords(e.target.value)}
        />
      </label>
      <section>
        <div className="text-sm text-slate-400 mb-1">Резюме (Markdown)</div>
        <MDEditor value={resume} onChange={(v) => setResume(v || "")} height={220} />
      </section>
      <section>
        <div className="text-sm text-slate-400 mb-1">Интервью / ответы</div>
        <MDEditor value={interview} onChange={(v) => setInterview(v || "")} height={220} />
      </section>
      <section>
        <div className="text-sm text-slate-400 mb-1">Трудовая история (расширенно)</div>
        <MDEditor value={workHistory} onChange={(v) => setWorkHistory(v || "")} height={220} />
      </section>
      <section>
        <div className="text-sm text-slate-400 mb-1">scoring_overrides (JSON)</div>
        <textarea
          className="w-full bg-slate-900 border border-slate-700 rounded p-2 font-mono text-xs h-40"
          value={weights}
          onChange={(e) => setWeights(e.target.value)}
        />
      </section>
      <div className="flex gap-2 flex-wrap">
        <button type="button" onClick={save} className="px-4 py-2 bg-blue-600 rounded">
          Сохранить
        </button>
        <button type="button" onClick={previewWeights} className="px-4 py-2 bg-slate-700 rounded">
          Preview весов
        </button>
      </div>
      {preview && (
        <pre className="text-xs bg-slate-950 p-3 rounded overflow-auto max-h-64">{preview}</pre>
      )}
      {msg && <p className="text-sm">{msg}</p>}
    </div>
  );
}
