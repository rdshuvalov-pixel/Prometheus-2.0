import { createServerSupabase } from "@/lib/supabase/server";
import { MarkApplied } from "./ui";

export default async function VacancyPage({ params }: { params: { id: string } }) {
  const supabase = await createServerSupabase();
  const { data: v } = await supabase.from("vacancies").select("*").eq("id", params.id).single();
  const { data: letters } = await supabase
    .from("cover_letters")
    .select("*")
    .eq("vacancy_id", params.id)
    .eq("kind", "formal");

  if (!v) return <p>Не найдено</p>;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">
        {v.company} — {v.role_title}
      </h1>
      <p className="text-slate-400">Score: {v.score ?? "—"} · {v.match_status}</p>
      <pre className="bg-slate-900 p-4 rounded text-xs overflow-auto max-h-96">
        {JSON.stringify(v.score_breakdown, null, 2)}
      </pre>
      <div>
        <h2 className="font-medium">Сопроводительное (formal)</h2>
        {(letters || []).length === 0 && (
          <p className="text-slate-500 text-sm">Пока нет письма. Запустите run_write.</p>
        )}
        {(letters || []).map((l: { kind: string; body: string }) => (
          <section key={l.kind} className="mt-2">
            <pre className="whitespace-pre-wrap text-sm bg-slate-900 p-2 rounded">{l.body}</pre>
          </section>
        ))}
      </div>
      <MarkApplied id={params.id} status={v.status} />
    </div>
  );
}
