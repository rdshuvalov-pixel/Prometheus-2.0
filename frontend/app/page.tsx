import Link from "next/link";
import { createServerSupabase } from "@/lib/supabase/server";

function formatTs(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Intl.DateTimeFormat("ru-RU", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

function durationMs(started: string | null | undefined, finished: string | null | undefined): string | null {
  if (!started || !finished) return null;
  try {
    const a = new Date(started).getTime();
    const b = new Date(finished).getTime();
    const ms = b - a;
    if (Number.isNaN(ms) || ms < 0) return null;
    if (ms < 60000) return `${Math.round(ms / 1000)} с`;
    const m = Math.floor(ms / 60000);
    const s = Math.round((ms % 60000) / 1000);
    return `${m} мин ${s} с`;
  } catch {
    return null;
  }
}

function payloadPreview(p: unknown): string {
  if (p == null) return "";
  try {
    const s = JSON.stringify(p);
    return s.length > 120 ? `${s.slice(0, 117)}…` : s;
  } catch {
    return String(p);
  }
}

function levelClass(level: string): string {
  const l = level.toLowerCase();
  if (l === "error") return "bg-red-900/50 text-red-200 border-red-700";
  if (l === "warn" || l === "warning") return "bg-amber-900/40 text-amber-100 border-amber-700";
  return "bg-slate-800 text-slate-300 border-slate-600";
}

export default async function HomePage() {
  const supabase = await createServerSupabase();
  const { data: runs } = await supabase
    .from("pipeline_runs")
    .select("*")
    .order("started_at", { ascending: false })
    .limit(1);

  const run = runs?.[0];

  const { data: events } = await supabase
    .from("pipeline_events")
    .select("ts, level, type, payload")
    .order("ts", { ascending: false })
    .limit(20);

  const metrics = (run?.metrics as Record<string, unknown> | null) ?? null;
  const dur = durationMs(run?.started_at, run?.finished_at);

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">Дашборд</h1>

      <section className="space-y-2">
        <h2 className="text-lg font-medium text-slate-200">Последний запуск</h2>
        {!run && <p className="text-slate-400">Нет данных pipeline_runs (проверьте RLS и логин).</p>}
        {run && (
          <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4 space-y-3">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <div>
                <p className="text-slate-100 font-medium">
                  {formatTs(run.started_at)} — <span className="text-slate-300">статус: {String(run.status)}</span>
                </p>
                {dur && <p className="text-sm text-slate-500">Длительность: {dur}</p>}
              </div>
              <span
                className={
                  String(run.status) === "ok"
                    ? "text-xs px-2 py-0.5 rounded border border-emerald-700 bg-emerald-900/30 text-emerald-200"
                    : "text-xs px-2 py-0.5 rounded border border-slate-600 bg-slate-800 text-slate-300"
                }
              >
                {String(run.status)}
              </span>
            </div>
            {run.finished_at && <p className="text-sm text-slate-500">Завершён: {formatTs(run.finished_at)}</p>}
            {metrics && Object.keys(metrics).length > 0 && (
              <div>
                <p className="text-sm text-slate-400 mb-1">Метрики</p>
                <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
                  {Object.entries(metrics).map(([k, v]) => (
                    <li key={k} className="flex justify-between gap-4 border-b border-slate-800/80 pb-1">
                      <span className="text-slate-500">{k}</span>
                      <span className="text-slate-200 font-mono text-right">{String(v)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <p className="text-xs text-slate-500 break-all">ID: {String(run.id)}</p>
            <p>
              <Link href={`/timeline?run_id=${run.id}`} className="text-sm text-blue-400 hover:underline">
                Все события запуска (Timeline)
              </Link>
            </p>
          </div>
        )}
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-medium text-slate-200">Последние события</h2>
        {(!events || events.length === 0) && <p className="text-slate-500 text-sm">Пока нет событий в pipeline_events.</p>}
        {events && events.length > 0 && (
          <ul className="space-y-2">
            {events.map(
              (e: { ts: string; level: string; type: string; payload: unknown }, i: number) => (
                <li
                  key={`${e.ts}-${e.type}-${i}`}
                  className="rounded border border-slate-800 bg-slate-900/30 px-3 py-2 text-sm"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <time className="text-slate-500 tabular-nums">{formatTs(e.ts)}</time>
                    <span
                      className={`text-xs px-1.5 py-0.5 rounded border ${levelClass(e.level || "info")}`}
                    >
                      {e.level}
                    </span>
                    <span className="text-slate-200 font-medium">{e.type}</span>
                  </div>
                  {e.payload != null &&
                    (typeof e.payload !== "object" ||
                      (e.payload !== null && Object.keys(e.payload as object).length > 0)) && (
                    <p className="mt-1 text-xs text-slate-500 font-mono break-all">{payloadPreview(e.payload)}</p>
                  )}
                </li>
              ),
            )}
          </ul>
        )}
      </section>
    </div>
  );
}
