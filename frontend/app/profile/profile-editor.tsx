"use client";

import { useEffect, useMemo, useState } from "react";
import MDEditor from "@uiw/react-md-editor";
import "@uiw/react-md-editor/markdown-editor.css";

type DocKind = "cv" | "description";
type DocRow = {
  id: string;
  kind: DocKind;
  file_name: string;
  uploaded_at: string;
  byte_size: number | null;
};

function formatBytes(n: number | null | undefined): string {
  if (!n || n <= 0) return "—";
  const kb = n / 1024;
  if (kb < 1024) return `${Math.round(kb)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
}

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

  const [docs, setDocs] = useState<DocRow[]>([]);
  const [docsMsg, setDocsMsg] = useState<string | null>(null);
  const [busyCv, setBusyCv] = useState(false);
  const [busyDesc, setBusyDesc] = useState(false);

  const cv = useMemo(() => docs.find((d) => d.kind === "cv") ?? null, [docs]);
  const desc = useMemo(() => docs.filter((d) => d.kind === "description"), [docs]);

  async function refreshDocs() {
    setDocsMsg(null);
    const r = await fetch("/api/profile/documents", { method: "GET" });
    if (!r.ok) {
      setDocsMsg(await r.text());
      return;
    }
    const data = (await r.json()) as { documents?: DocRow[] };
    setDocs(Array.isArray(data.documents) ? data.documents : []);
  }

  useEffect(() => {
    void refreshDocs();
  }, []);

  async function uploadDoc(kind: DocKind, file: File) {
    setDocsMsg(null);
    const form = new FormData();
    form.set("kind", kind);
    form.set("file", file);
    const r = await fetch("/api/profile/documents", { method: "POST", body: form });
    if (!r.ok) {
      const t = await r.text();
      setDocsMsg(t);
      return;
    }
    await refreshDocs();
  }

  async function deleteDesc(id: string) {
    setDocsMsg(null);
    const r = await fetch(`/api/profile/documents/${id}`, { method: "DELETE" });
    if (!r.ok) {
      setDocsMsg(await r.text());
      return;
    }
    await refreshDocs();
  }

  async function save() {
    let overrides: unknown = null;
    try {
      overrides = weights.trim() ? JSON.parse(weights) : null;
    } catch {
      setMsg("Invalid JSON in scoring_overrides");
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
    setMsg(r.ok ? "Saved" : await r.text());
  }

  async function previewWeights() {
    let overrides: unknown = null;
    try {
      overrides = weights.trim() ? JSON.parse(weights) : null;
    } catch {
      setPreview("Invalid JSON in scoring_overrides");
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
      <section className="rounded border border-slate-700 bg-slate-950/40 p-3">
        <div className="flex items-baseline justify-between gap-2 flex-wrap">
          <h2 className="text-sm font-semibold text-slate-200">Documents</h2>
          <span className="text-xs text-slate-400">PDF/DOCX/TXT/MD · max 5MB</span>
        </div>

        <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="rounded border border-slate-800 bg-slate-950/40 p-3">
            <div className="flex items-baseline justify-between gap-2">
              <div>
                <div className="text-sm font-semibold text-slate-200">Master CV</div>
                <div className="text-xs text-slate-400">Single file. Replace-only. Cannot be deleted.</div>
              </div>
              <button
                type="button"
                onClick={() => void refreshDocs()}
                className="text-xs px-2 py-1 rounded bg-slate-800 text-slate-200"
              >
                Refresh
              </button>
            </div>

            <div className="mt-3">
              {cv ? (
                <div className="text-xs text-slate-300">
                  <div className="font-mono break-all">{cv.file_name}</div>
                  <div className="text-slate-400">
                    {new Date(cv.uploaded_at).toLocaleString("en-US")} · {formatBytes(cv.byte_size)}
                  </div>
                </div>
              ) : (
                <div className="text-xs text-amber-300">No CV uploaded yet.</div>
              )}
            </div>

            <div className="mt-3 flex items-center gap-2">
              <input
                type="file"
                className="text-xs text-slate-300"
                disabled={busyCv}
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (!f) return;
                  setBusyCv(true);
                  void uploadDoc("cv", f).finally(() => setBusyCv(false));
                }}
              />
            </div>
          </div>

          <div className="rounded border border-slate-800 bg-slate-950/40 p-3">
            <div className="flex items-baseline justify-between gap-2">
              <div>
                <div className="text-sm font-semibold text-slate-200">Additional materials</div>
                <div className="text-xs text-slate-400">Optional. Up to 3 files. Can be deleted.</div>
              </div>
              <div className="text-xs text-slate-400">{desc.length}/3</div>
            </div>

            <div className="mt-3 flex items-center gap-2">
              <input
                type="file"
                className="text-xs text-slate-300"
                disabled={busyDesc || desc.length >= 3}
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (!f) return;
                  setBusyDesc(true);
                  void uploadDoc("description", f).finally(() => setBusyDesc(false));
                }}
              />
            </div>

            <div className="mt-3 space-y-2">
              {desc.length === 0 ? (
                <div className="text-xs text-slate-400">No additional documents.</div>
              ) : (
                desc.map((d) => (
                  <div key={d.id} className="flex items-start justify-between gap-3 rounded border border-slate-800 p-2">
                    <div className="min-w-0">
                      <div className="text-xs text-slate-200 font-mono break-all">{d.file_name}</div>
                      <div className="text-[11px] text-slate-400">
                        {new Date(d.uploaded_at).toLocaleString("en-US")} · {formatBytes(d.byte_size)}
                      </div>
                    </div>
                    <button
                      type="button"
                      className="text-xs px-2 py-1 rounded bg-red-600/20 text-red-200 border border-red-900/40"
                      onClick={() => void deleteDesc(d.id)}
                    >
                      Delete
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {docsMsg && <p className="mt-3 text-xs text-amber-300 break-all">{docsMsg}</p>}
      </section>

      <label className="block">
        <span className="text-sm text-slate-400">Profession</span>
        <input
          className="w-full bg-slate-900 border border-slate-700 rounded p-2 mt-1"
          value={profession}
          onChange={(e) => setProfession(e.target.value)}
        />
      </label>
      <label className="block">
        <span className="text-sm text-slate-400">Search keywords (comma-separated)</span>
        <input
          className="w-full bg-slate-900 border border-slate-700 rounded p-2 mt-1"
          value={keywords}
          onChange={(e) => setKeywords(e.target.value)}
        />
      </label>
      <section>
        <div className="text-sm text-slate-400 mb-1">Resume (Markdown)</div>
        <MDEditor value={resume} onChange={(v) => setResume(v || "")} height={220} />
      </section>
      <section>
        <div className="text-sm text-slate-400 mb-1">Interview notes</div>
        <MDEditor value={interview} onChange={(v) => setInterview(v || "")} height={220} />
      </section>
      <section>
        <div className="text-sm text-slate-400 mb-1">Work history (expanded)</div>
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
          Save
        </button>
        <button type="button" onClick={previewWeights} className="px-4 py-2 bg-slate-700 rounded">
          Preview weights
        </button>
      </div>
      {preview && (
        <pre className="text-xs bg-slate-950 p-3 rounded overflow-auto max-h-64">{preview}</pre>
      )}
      {msg && <p className="text-sm">{msg}</p>}
    </div>
  );
}
