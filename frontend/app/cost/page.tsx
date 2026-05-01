import { createClient } from "@supabase/supabase-js";

export default async function CostPage() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY!;
  if (!url || !key) {
    return <p>Задайте SUPABASE_SERVICE_ROLE_KEY для серверной агрегации.</p>;
  }
  const supabase = createClient(url, key);
  const { data: calls } = await supabase.from("llm_calls").select("model, cost, tokens_in, tokens_out").limit(5000);

  const byModel: Record<string, number> = {};
  for (const c of calls || []) {
    const m = (c as { model?: string }).model || "?";
    const cost = Number((c as { cost?: number }).cost || 0);
    byModel[m] = (byModel[m] || 0) + cost;
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">LLM cost (агрегат)</h1>
      <pre className="bg-slate-900 p-4 rounded text-sm">{JSON.stringify(byModel, null, 2)}</pre>
    </div>
  );
}
