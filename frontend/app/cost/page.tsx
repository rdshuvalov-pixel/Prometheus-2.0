import { createServerSupabase } from "@/lib/supabase/server";

type CallRow = {
  model: string | null;
  function: string | null;
  cost: number | null;
  tokens_in: number | null;
  tokens_out: number | null;
};

type Agg = {
  calls: number;
  tokens_in: number;
  tokens_out: number;
  cost_usd: number;
};

function emptyAgg(): Agg {
  return { calls: 0, tokens_in: 0, tokens_out: 0, cost_usd: 0 };
}

function aggBy(rows: CallRow[], key: "model" | "function"): Map<string, Agg> {
  const out = new Map<string, Agg>();
  for (const r of rows) {
    const k = (r[key] as string | null) || "—";
    const a = out.get(k) ?? emptyAgg();
    a.calls += 1;
    a.tokens_in += Number(r.tokens_in || 0);
    a.tokens_out += Number(r.tokens_out || 0);
    a.cost_usd += Number(r.cost || 0);
    out.set(k, a);
  }
  return out;
}

function totals(rows: CallRow[]): Agg {
  const t = emptyAgg();
  for (const r of rows) {
    t.calls += 1;
    t.tokens_in += Number(r.tokens_in || 0);
    t.tokens_out += Number(r.tokens_out || 0);
    t.cost_usd += Number(r.cost || 0);
  }
  return t;
}

function fmtUsd(n: number): string {
  return `$${n.toFixed(4)}`;
}

function fmtInt(n: number): string {
  return new Intl.NumberFormat("ru-RU").format(n);
}

function Table({ label, data }: { label: string; data: Map<string, Agg> }) {
  const rows = Array.from(data.entries()).sort((a, b) => b[1].cost_usd - a[1].cost_usd);
  return (
    <section className="space-y-2">
      <h2 className="text-lg font-medium text-neutral-900">{label}</h2>
      <div className="overflow-x-auto rounded border border-neutral-200 bg-white/90 shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-neutral-100 text-neutral-900">
            <tr>
              <th className="text-left px-3 py-2">{label}</th>
              <th className="text-right px-3 py-2">Calls</th>
              <th className="text-right px-3 py-2">Tokens in</th>
              <th className="text-right px-3 py-2">Tokens out</th>
              <th className="text-right px-3 py-2">Cost USD</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr>
                <td colSpan={5} className="text-center text-neutral-600 py-3">
                  Нет данных
                </td>
              </tr>
            )}
            {rows.map(([k, a]) => (
              <tr key={k} className="border-t border-neutral-200">
                <td className="px-3 py-2 text-neutral-900 font-mono">{k}</td>
                <td className="px-3 py-2 text-right tabular-nums">{fmtInt(a.calls)}</td>
                <td className="px-3 py-2 text-right tabular-nums">{fmtInt(a.tokens_in)}</td>
                <td className="px-3 py-2 text-right tabular-nums">{fmtInt(a.tokens_out)}</td>
                <td className="px-3 py-2 text-right tabular-nums">{fmtUsd(a.cost_usd)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default async function CostPage() {
  const supabase = await createServerSupabase();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return <p className="text-neutral-900">Войдите в систему, чтобы увидеть LLM cost.</p>;
  }
  const { data, error } = await supabase
    .from("llm_calls")
    .select("model, function, cost, tokens_in, tokens_out")
    .order("id", { ascending: false })
    .limit(5000);
  if (error) {
    return (
      <p className="text-neutral-900">
        Не удалось загрузить llm_calls ({error.message}). Проверьте RLS таблицы.
      </p>
    );
  }

  const calls = (data || []) as CallRow[];
  const total = totals(calls);
  const byModel = aggBy(calls, "model");
  const byFunction = aggBy(calls, "function");

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-neutral-900">LLM cost</h1>

      <section className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="rounded border border-neutral-200 bg-white/90 shadow-sm p-3">
          <p className="text-xs text-neutral-600 font-medium">Calls</p>
          <p className="text-xl font-semibold tabular-nums text-neutral-900">{fmtInt(total.calls)}</p>
        </div>
        <div className="rounded border border-neutral-200 bg-white/90 shadow-sm p-3">
          <p className="text-xs text-neutral-600 font-medium">Tokens in</p>
          <p className="text-xl font-semibold tabular-nums text-neutral-900">{fmtInt(total.tokens_in)}</p>
        </div>
        <div className="rounded border border-neutral-200 bg-white/90 shadow-sm p-3">
          <p className="text-xs text-neutral-600 font-medium">Tokens out</p>
          <p className="text-xl font-semibold tabular-nums text-neutral-900">{fmtInt(total.tokens_out)}</p>
        </div>
        <div className="rounded border border-neutral-200 bg-white/90 shadow-sm p-3">
          <p className="text-xs text-neutral-600 font-medium">Cost USD</p>
          <p className="text-xl font-semibold tabular-nums text-neutral-900">{fmtUsd(total.cost_usd)}</p>
        </div>
      </section>

      <Table label="По моделям" data={byModel} />
      <Table label="По функциям" data={byFunction} />

      <p className="text-xs text-neutral-600">
        Прайсы заданы в backend/llm/models.yaml; если для модели цена отсутствует, cost логируется как NULL.
      </p>
    </div>
  );
}
