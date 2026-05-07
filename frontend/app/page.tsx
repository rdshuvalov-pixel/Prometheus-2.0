import Link from "next/link";
import { createServerSupabase } from "@/lib/supabase/server";
import DescriptionPanel from "./DescriptionPanel";
import { StepButtons } from "./StepButtons";

function formatTs(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Intl.DateTimeFormat("en-US", {
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
    if (ms < 60000) return `${Math.round(ms / 1000)}s`;
    const m = Math.floor(ms / 60000);
    const s = Math.round((ms % 60000) / 1000);
    return `${m}m ${s}s`;
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
  return "bg-neutral-100 text-neutral-800 border-neutral-300";
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

  const startPayload =
    startEv?.payload != null && typeof startEv.payload === "object" && startEv.payload !== null
      ? (startEv.payload as Record<string, unknown>)
      : null;

  const targetsRaw = startPayload?.targets;
  const targets =
    typeof targetsRaw === "number"
      ? targetsRaw
      : targetsRaw != null && !Number.isNaN(Number(targetsRaw))
        ? Number(targetsRaw)
        : null;

  const crawlTier = startPayload?.tier != null ? String(startPayload.tier) : null;
  const targetsTotalYaml =
    typeof startPayload?.targets_total_yaml === "number"
      ? startPayload.targets_total_yaml
      : startPayload?.targets_total_yaml != null && !Number.isNaN(Number(startPayload.targets_total_yaml))
        ? Number(startPayload.targets_total_yaml)
        : null;
  const crawlLimit =
    typeof startPayload?.limit === "number"
      ? startPayload.limit
      : startPayload?.limit != null && !Number.isNaN(Number(startPayload.limit))
        ? Number(startPayload.limit)
        : null;

  const { count: crawlErrorCount } = runId
    ? await supabase
        .from("pipeline_events")
        .select("*", { count: "exact", head: true })
        .eq("run_id", runId)
        .eq("type", "crawl_error")
    : { count: null };

  const { data: targetsDoneRows } = runId
    ? await supabase
        .from("pipeline_events")
        .select("ts, payload")
        .eq("run_id", runId)
        .eq("type", "target_done")
        .order("ts", { ascending: true })
    : { data: null };

  const { data: events } = runId
    ? await supabase
        .from("pipeline_events")
        .select("ts, level, type, payload")
        .eq("run_id", runId)
        .order("ts", { ascending: false })
        .limit(200)
    : { data: null };

  const metrics = (run?.metrics as Record<string, unknown> | null) ?? null;
  const dur = durationMs(run?.started_at, run?.finished_at);

  type TargetDone = {
    company: string;
    raws: number;
    kept: number;
    rejected: number;
    by_reason: Record<string, number>;
    errored: boolean;
  };

  function topReason(by: Record<string, number> | null | undefined): string {
    if (!by) return "—";
    const entries = Object.entries(by);
    if (entries.length === 0) return "—";
    entries.sort((a, b) => b[1] - a[1]);
    const [code, n] = entries[0];
    return `${code} (${n})`;
  }

  const targetsDone: TargetDone[] = (targetsDoneRows ?? [])
    .map((r) => {
      const p = (r.payload ?? {}) as Record<string, unknown>;
      return {
        company: typeof p.company === "string" ? p.company : "—",
        raws: Number(p.raws ?? 0),
        kept: Number(p.kept ?? 0),
        rejected: Number(p.rejected ?? 0),
        by_reason: (p.by_reason as Record<string, number> | undefined) ?? {},
        errored: Boolean(p.errored),
      } as TargetDone;
    })
    .sort((a, b) => b.kept - a.kept || b.rejected - a.rejected);

  const totalTargets = targetsDone.length;
  const targetsWithKept = targetsDone.filter((t) => t.kept > 0).length;
  const targetsZero = targetsDone.filter((t) => t.raws === 0 && !t.errored).length;
  const reasonAgg: Record<string, number> = {};
  for (const t of targetsDone) {
    for (const [k, v] of Object.entries(t.by_reason)) {
      reasonAgg[k] = (reasonAgg[k] ?? 0) + Number(v);
    }
  }
  const topGlobalReason = topReason(reasonAgg);

  return (
    <div className="space-y-8">
      <DescriptionPanel />

      <h1 className="text-2xl font-semibold text-neutral-900">Dashboard</h1>

      <section className="space-y-2">
        <h2 className="text-lg font-medium text-neutral-900">Last run</h2>
        {!run && (
          <p className="text-neutral-700">No data in pipeline_runs (check RLS and sign-in).</p>
        )}
        {run && (
          <div className="rounded-lg border border-neutral-200 bg-white/90 shadow-sm p-4 space-y-3">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <div>
                <p className="text-neutral-900 font-medium">
                  {formatTs(run.started_at)} —{" "}
                  <span className="text-neutral-700">status: {String(run.status)}</span>
                </p>
                {dur && <p className="text-sm text-neutral-600">Duration: {dur}</p>}
              </div>
              <span
                className={
                  String(run.status) === "ok"
                    ? "text-xs px-2 py-0.5 rounded border border-emerald-200 bg-emerald-50 text-emerald-900 font-medium"
                    : "text-xs px-2 py-0.5 rounded border border-neutral-300 bg-neutral-100 text-neutral-800 font-medium"
                }
              >
                {String(run.status)}
              </span>
            </div>
            {run.finished_at && (
              <p className="text-sm text-neutral-600">Finished: {formatTs(run.finished_at)}</p>
            )}

            <div className="rounded border border-neutral-200 bg-gradient-to-br from-white to-[#fff7fa] p-3 text-sm space-y-1">
              <p className="font-semibold text-neutral-900 mb-2">Run summary</p>
              <p className="flex justify-between gap-4">
                <span className="text-neutral-700">Targets in tier (from YAML)</span>
                <span className="font-mono tabular-nums font-medium text-neutral-900">{targets ?? "—"}</span>
              </p>
              <p className="flex justify-between gap-4">
                <span className="text-neutral-700">Found vacancies</span>
                <span className="font-mono tabular-nums font-medium text-neutral-900">
                  {metricStr(metrics, "processed")}
                </span>
              </p>
              <p className="flex justify-between gap-4">
                <span className="text-neutral-700">Passed filter</span>
                <span className="font-mono tabular-nums font-medium text-neutral-900">
                  {metricStr(metrics, "kept")}
                </span>
              </p>
              <p className="flex justify-between gap-4">
                <span className="text-neutral-700">Rejected</span>
                <span className="font-mono tabular-nums font-medium text-neutral-900">
                  {metricStr(metrics, "rejected")}
                </span>
              </p>
              <p className="flex justify-between gap-4">
                <span className="text-neutral-700">Crawler errors</span>
                <span className="font-mono tabular-nums font-medium text-neutral-900">
                  {crawlErrorCount ?? "—"}
                </span>
              </p>
              <p className="text-xs text-neutral-600 leading-relaxed border-t border-neutral-200 pt-2 mt-2">
                <strong className="text-neutral-800">How targets are counted:</strong> only goals for the selected tier in{" "}
                <code className="rounded bg-neutral-100 px-1 font-mono text-neutral-900">targets.yaml</code>, не сумма по
                tier&nbsp;2–4 и не «все сайты подряд».
                {targets != null && targetsTotalYaml != null && (
                  <>
                    {" "}
                    Для этого запуска: <strong>{targets}</strong> целей в tier
                    {crawlTier ? ` «${crawlTier}»` : ""}, всего строк в YAML <strong>{targetsTotalYaml}</strong>.
                  </>
                )}
                {crawlLimit != null && crawlLimit > 0 && (
                  <>
                    {" "}
                    За один проход краулер реально обходит не более <strong>{crawlLimit}</strong> целей (
                    <code className="rounded bg-neutral-100 px-1 font-mono text-neutral-900">--limit</code>
                    ).
                  </>
                )}
              </p>
            </div>

            <StepButtons />

            {totalTargets > 0 && (
              <details className="group rounded border border-neutral-200 bg-white p-3 text-sm">
                <summary className="cursor-pointer list-none flex flex-wrap items-baseline justify-between gap-2 [&::-webkit-details-marker]:hidden">
                  <span className="font-semibold text-neutral-900">
                    <span className="mr-1 text-neutral-500 group-open:hidden">▸</span>
                    <span className="mr-1 text-neutral-500 hidden group-open:inline">▾</span>
                    По площадкам ({totalTargets})
                  </span>
                  <span className="text-xs text-neutral-600">
                    kept у <strong>{targetsWithKept}</strong>; пусто у <strong>{targetsZero}</strong>; топ причина:{" "}
                    <strong>{topGlobalReason}</strong>
                  </span>
                </summary>
                <div className="mt-3 overflow-x-auto rounded border border-neutral-200">
                  <table className="w-full text-xs">
                    <thead className="bg-neutral-100 text-neutral-900">
                      <tr>
                        <th className="text-left px-2 py-1">Компания</th>
                        <th className="text-right px-2 py-1">Найдено</th>
                        <th className="text-right px-2 py-1">Kept</th>
                        <th className="text-right px-2 py-1">Rejected</th>
                        <th className="text-left px-2 py-1">Топ причина</th>
                      </tr>
                    </thead>
                    <tbody>
                      {targetsDone.map((t, i) => (
                        <tr
                          key={`${t.company}-${i}`}
                          className={
                            "border-t border-neutral-200 " +
                            (t.errored
                              ? "bg-red-50 text-red-900"
                              : t.raws === 0
                                ? "text-neutral-500"
                                : "text-neutral-900")
                          }
                        >
                          <td className="px-2 py-1 font-medium">{t.company}</td>
                          <td className="px-2 py-1 text-right tabular-nums">{t.raws}</td>
                          <td className="px-2 py-1 text-right tabular-nums">{t.kept}</td>
                          <td className="px-2 py-1 text-right tabular-nums">{t.rejected}</td>
                          <td className="px-2 py-1 font-mono text-[11px]">{t.errored ? "error" : topReason(t.by_reason)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
            )}

            {metrics && Object.keys(metrics).length > 0 && (
              <div>
                <p className="text-sm text-neutral-700 mb-1 font-medium">Метрики (сырой JSON)</p>
                <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
                  {Object.entries(metrics).map(([k, v]) => (
                    <li key={k} className="flex justify-between gap-4 border-b border-neutral-200 pb-1">
                      <span className="text-neutral-600">{k}</span>
                      <span className="text-neutral-900 font-mono text-right">{String(v)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <p className="text-xs text-neutral-600 break-all">ID: {String(run.id)}</p>
            <p>
              <Link
                href={`/timeline?run_id=${run.id}`}
                className="text-sm font-medium text-candy-800 hover:text-candy-600 hover:underline"
              >
                Все события запуска (Timeline)
              </Link>
            </p>
          </div>
        )}
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-medium text-neutral-900">Run log</h2>
        {(!runId || !events || events.length === 0) && (
          <p className="text-neutral-700 text-sm">No events for the last run yet.</p>
        )}
        {runId && events && events.length > 0 && (
          <details className="group rounded-lg border border-neutral-200 bg-white/90 shadow-sm">
            <summary className="cursor-pointer list-none flex flex-wrap items-center justify-between gap-2 px-4 py-3 [&::-webkit-details-marker]:hidden">
              <div className="flex items-center gap-2">
                <span className="text-neutral-500 group-open:hidden">▸</span>
                <span className="text-neutral-500 hidden group-open:inline">▾</span>
                <span className="font-semibold text-neutral-900">Run log</span>
                <span className="text-xs text-neutral-600">({events.length} events)</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="rounded border border-neutral-200 bg-neutral-100 px-2 py-0.5 text-neutral-800 font-medium">
                  errors: {events.filter((e) => String(e.level || "").toLowerCase() === "error").length}
                </span>
                <span className="rounded border border-neutral-200 bg-neutral-100 px-2 py-0.5 text-neutral-800 font-medium">
                  warnings: {events.filter((e) => ["warn", "warning"].includes(String(e.level || "").toLowerCase())).length}
                </span>
              </div>
            </summary>
            <div className="border-t border-neutral-200">
              <div className="max-h-[420px] overflow-auto">
                <ul className="divide-y divide-neutral-200">
                  {events.map((e: { ts: string; level: string; type: string; payload: unknown }, i: number) => (
                    <li key={`${e.ts}-${e.type}-${i}`} className="px-4 py-2 text-xs">
                      <div className="flex flex-wrap items-center gap-2">
                        <time className="text-neutral-600 tabular-nums">{formatTs(e.ts)}</time>
                        <span className={`text-[11px] px-1.5 py-0.5 rounded border ${levelClass(e.level || "info")}`}>
                          {String(e.level || "info")}
                        </span>
                        <span className="text-neutral-900 font-semibold">{e.type}</span>
                      </div>
                      {e.payload != null &&
                        (typeof e.payload !== "object" ||
                          (e.payload !== null && Object.keys(e.payload as object).length > 0)) && (
                          <p className="mt-1 text-[11px] text-neutral-700 font-mono break-all">
                            {payloadPreview(e.payload)}
                          </p>
                        )}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="px-4 py-3 text-sm">
                <Link
                  href={`/timeline?run_id=${runId}`}
                  className="font-medium text-candy-800 hover:text-candy-600 hover:underline"
                >
                  View full timeline
                </Link>
              </div>
            </div>
          </details>
        )}
      </section>
    </div>
  );
}
