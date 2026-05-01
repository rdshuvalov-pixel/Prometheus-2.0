import { createServerSupabase } from "@/lib/supabase/server";

export default async function HomePage() {
  const supabase = await createServerSupabase();
  const { data: runs } = await supabase
    .from("pipeline_runs")
    .select("*")
    .order("started_at", { ascending: false })
    .limit(1);

  const run = runs?.[0];

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Последний запуск</h1>
      {!run && <p className="text-slate-400">Нет данных pipeline_runs (проверьте RLS и логин).</p>}
      {run && (
        <pre className="bg-slate-900 p-4 rounded text-xs overflow-auto">
          {JSON.stringify(run, null, 2)}
        </pre>
      )}
    </div>
  );
}
