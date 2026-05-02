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
  if (l === "error") return "bg-red-50 text-red-800 border-red-200";
  if (l === "warn" || l === "warning") return "bg-amber-50 text-amber-900 border-amber-200";
  return "bg-candy-100 text-candy-700 border-candy-200";
}

function metricStr(metrics: Record<string, unknown> | null, key: string): string {
  if (!metrics || !(key in metrics)) return "—";
  return String(metrics[key]);
}

export default async function HomePage() {
  const supabase = await createServerSupabase();
  const { data: runs } = await supabase
    .from("pipeline_runs")
    .select("*")
    .order("started_at", { ascending: false })
    .limit(1);

  const run = runs?.[0];
  const runId = run?.id as string | undefined;

  const { data: startEv } = runId
    ? await supabase
        .from("pipeline_events")
        .select("payload")
        .eq("run_id", runId)
        .eq("type", "crawl_started")
        .order("ts", { ascending: true })
        .limit(1)
        .maybeSingle()
    : { data: null };

  const targetsRaw =
    startEv?.payload != null &&
    typeof startEv.payload === "object" &&
    startEv.payload !== null &&
    "targets" in startEv.payload
      ? (startEv.payload as { targets?: unknown }).targets
      : null;
  const targets =
    typeof targetsRaw === "number"
      ? targetsRaw
      : targetsRaw != null && !Number.isNaN(Number(targetsRaw))
        ? Number(targetsRaw)
        : null;

  const { count: crawlErrorCount } = runId
    ? await supabase
        .from("pipeline_events")
        .select("*", { count: "exact", head: true })
        .eq("run_id", runId)
        .eq("type", "crawl_error")
    : { count: null };

  const { data: events } = await supabase
    .from("pipeline_events")
    .select("ts, level, type, payload")
    .order("ts", { ascending: false })
    .limit(20);

  const metrics = (run?.metrics as Record<string, unknown> | null) ?? null;
  const dur = durationMs(run?.started_at, run?.finished_at);

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold text-candy-700">Дашборд</h1>

      <section className="space-y-2">
        <h2 className="text-lg font-medium text-candy-700">Последний запуск</h2>
        {!run && (
          <p className="text-candy-600">Нет данных pipeline_runs (проверьте RLS и логин).</p>
        )}
        {run && (
          <div className="rounded-lg border border-candy-200 bg-white/70 p-4 space-y-3">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <div>
                <p className="text-candy-700 font-medium">
                  {formatTs(run.started_at)} —{" "}
                  <span className="text-candy-600">статус: {String(run.status)}</span>
                </p>
                {dur && <p className="text-sm text-candy-600">Длительность: {dur}</p>}
              </div>
              <span
                className={
                  String(run.status) === "ok"
                    ? "text-xs px-2 py-0.5 rounded border border-emerald-200 bg-emerald-50 text-emerald-800"
                    : "text-xs px-2 py-0.5 rounded border border-candy-200 bg-candy-100 text-candy-700"
                }
              >
                {String(run.status)}
              </span>
            </div>
            {run.finished_at && (
              <p className="text-sm text-candy-600">Завершён: {formatTs(run.finished_at)}</p>
            )}

            <div className="rounded border border-candy-200 bg-candy-50/80 p-3 text-sm space-y-1">
              <p className="font-medium text-candy-700 mb-2">Сводка прогона</p>
              <p className="flex justify-between gap-4">
                <span className="text-candy-600">Площадок (целей crawl)</span>
                <span className="font-mono tabular-nums text-candy-700">{targets ?? "—"}</span>
              </p>
              <p className="flex justify-between gap-4">
                <span className="text-candy-600">Найдено вакансий</span>
                <span className="font-mono tabular-nums text-candy-700">
                  {metricStr(metrics, "processed")}
                </span>
              </p>
              <p className="flex justify-between gap-4">
                <span className="text-candy-600">Прошло фильтр</span>
                <span className="font-mono tabular-nums text-candy-700">{metricStr(metrics, "kept")}</span>
              </p>
              <p className="flex justify-between gap-4">
                <span className="text-candy-600">Отклонено</span>
                <span className="font-mono tabular-nums text-candy-700">
                  {metricStr(metrics, "rejected")}
                </span>
              </p>
              <p className="flex justify-between gap-4">
                <span className="text-candy-600">Ошибок краулера</span>
                <span className="font-mono tabular-nums text-candy-700">
                  {crawlErrorCount ?? "—"}
                </span>
              </p>
            </div>

            {metrics && Object.keys(metrics).length > 0 && (
              <div>
                <p className="text-sm text-candy-600 mb-1">Метрики (сырой JSON)</p>
                <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
                  {Object.entries(metrics).map(([k, v]) => (
                    <li key={k} className="flex justify-between gap-4 border-b border-candy-200/80 pb-1">
                      <span className="text-candy-600">{k}</span>
                      <span className="text-candy-700 font-mono text-right">{String(v)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <p className="text-xs text-candy-600 break-all">ID: {String(run.id)}</p>
            <p>
              <Link
                href={`/timeline?run_id=${run.id}`}
                className="text-sm text-candy-600 hover:text-candy-500 hover:underline"
              >
                Все события запуска (Timeline)
              </Link>
            </p>
          </div>
        )}
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-medium text-candy-700">Последние события</h2>
        {(!events || events.length === 0) && (
          <p className="text-candy-600 text-sm">Пока нет событий в pipeline_events.</p>
        )}
        {events && events.length > 0 && (
          <ul className="space-y-2">
            {events.map(
              (e: { ts: string; level: string; type: string; payload: unknown }, i: number) => (
                <li
                  key={`${e.ts}-${e.type}-${i}`}
                  className="rounded border border-candy-200 bg-white/70 px-3 py-2 text-sm"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <time className="text-candy-600 tabular-nums">{formatTs(e.ts)}</time>
                    <span className={`text-xs px-1.5 py-0.5 rounded border ${levelClass(e.level || "info")}`}>
                      {e.level}
                    </span>
                    <span className="text-candy-700 font-medium">{e.type}</span>
                  </div>
                  {e.payload != null &&
                    (typeof e.payload !== "object" ||
                      (e.payload !== null && Object.keys(e.payload as object).length > 0)) && (
                      <p className="mt-1 text-xs text-candy-600 font-mono break-all">
                        {payloadPreview(e.payload)}
                      </p>
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
