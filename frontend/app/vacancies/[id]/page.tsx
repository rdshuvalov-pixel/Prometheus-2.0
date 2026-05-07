import type { ReactNode } from "react";
import { createServerSupabase } from "@/lib/supabase/server";
import { GenerateFormal, MarkApplied } from "./ui";

const REJECT_HINTS: Record<string, string> = {
  country_blacklisted: "Стоп-лист локаций (Cyprus/Georgia и др.) без явного EU-remote.",
  hybrid_outside_lisbon: "Hybrid вне Лиссабона.",
  below_threshold: "Скоринг ниже порога или группа A не прошла.",
  us_only: "Регион не подходит / US-only.",
  office_only: "Только офис.",
  not_product_role: "Не продуктовая роль.",
};

function Row({ ok, children }: { ok: boolean; children: ReactNode }) {
  return (
    <div className="flex items-start gap-2 text-sm">
      <span className={ok ? "font-semibold text-emerald-700 shrink-0" : "text-neutral-400 shrink-0"} aria-hidden>
        {ok ? "✓" : "○"}
      </span>
      <div className="text-neutral-800">{children}</div>
    </div>
  );
}

export default async function VacancyPage({ params }: { params: { id: string } }) {
  const supabase = await createServerSupabase();
  const { data: v } = await supabase.from("vacancies").select("*").eq("id", params.id).single();
  const { data: letters } = await supabase
    .from("cover_letters")
    .select("*")
    .eq("vacancy_id", params.id)
    .eq("kind", "formal");

  if (!v) return <p className="text-neutral-700">Не найдено</p>;

  const desc = typeof v.description === "string" ? v.description : "";
  const descLen = desc.trim().length;
  const hasFormal = Array.isArray(letters) && letters.length > 0;

  const warnings = Array.isArray(v.warnings) ? (v.warnings as string[]) : [];
  const rr = v.reject_reason != null ? String(v.reject_reason) : null;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-neutral-900">
        {v.company} — {v.role_title}
      </h1>

      <section className="rounded-lg border border-neutral-200 bg-white/90 shadow-sm p-4 space-y-3">
        <h2 className="font-semibold text-neutral-900">Заполнение полей</h2>
        <p className="text-xs text-neutral-600">
          Обогащение и скоринг по умолчанию только для вакансий с <code className="rounded bg-neutral-100 px-1">created_at</code> от
          сегодня (UTC); короткое описание помечается предупреждением <code className="rounded bg-neutral-100 px-1">short_description</code>.
        </p>
        <div className="space-y-2 border-t border-neutral-200 pt-3">
          <Row ok={descLen >= 100}>
            <span>
              Описание (JD): {descLen === 0 ? "пусто" : `${descLen} симв.`}
              {descLen > 0 && descLen < 100 ? " — мало текста для LLM-обогащения" : ""}
            </span>
          </Row>
          <Row ok={v.posted_at != null}>
            <span>Дата публикации: {v.posted_at != null ? String(v.posted_at) : "не известна"}</span>
          </Row>
          <Row ok={v.employment_type != null && String(v.employment_type).trim() !== ""}>
            <span>Тип занятости: {v.employment_type != null ? String(v.employment_type) : "—"}</span>
          </Row>
          <Row ok={v.enrichment_at != null}>
            <span>Обогащение (LLM): {v.enrichment_at != null ? String(v.enrichment_at) : "ещё не запускалось / короткое описание"}</span>
          </Row>
          <Row ok={v.score != null}>
            <span>
              Скоринг: {v.score != null ? `${v.score} · ${v.match_status ?? "—"}` : "нет (нет данных или очередь)"}
            </span>
          </Row>
          <Row ok={hasFormal}>
            <span>Сопроводительное formal: {hasFormal ? "есть" : "нет — запустите run_write для Scored ≥50"}</span>
          </Row>
        </div>
        {(warnings.length > 0 || rr) && (
          <div className="border-t border-neutral-200 pt-3 text-sm space-y-1">
            {warnings.length > 0 && (
              <p className="text-neutral-700">
                <span className="font-medium">Предупреждения:</span> {warnings.join(", ")}
              </p>
            )}
            {rr && (
              <p className="text-neutral-700">
                <span className="font-medium">Причина отсева:</span> {rr}
                {REJECT_HINTS[rr] ? ` — ${REJECT_HINTS[rr]}` : ""}
              </p>
            )}
          </div>
        )}
      </section>

      <p className="text-neutral-600">
        Score: <span className="font-medium text-neutral-900">{v.score ?? "—"}</span> · {String(v.match_status ?? "—")}
      </p>
      <pre className="bg-neutral-900 text-neutral-100 p-4 rounded text-xs overflow-auto max-h-96">
        {JSON.stringify(v.score_breakdown, null, 2)}
      </pre>
      <div>
        <h2 className="font-medium text-neutral-900">Сопроводительное (formal)</h2>
        {(letters || []).length === 0 && (
          <div className="space-y-2">
            <p className="text-neutral-600 text-sm">Пока нет письма. Можно сгенерировать по кнопке.</p>
            <GenerateFormal id={params.id} />
          </div>
        )}
        {(letters || []).map((l: { kind: string; body: string }) => (
          <section key={l.kind} className="mt-2">
            <pre className="whitespace-pre-wrap text-sm bg-white/90 border border-neutral-200 rounded p-3 text-neutral-900">
              {l.body}
            </pre>
          </section>
        ))}
      </div>
      <MarkApplied id={params.id} status={v.status} />
    </div>
  );
}
