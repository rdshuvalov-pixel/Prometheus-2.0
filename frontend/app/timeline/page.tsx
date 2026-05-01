import { createServerSupabase } from "@/lib/supabase/server";

export default async function TimelinePage() {
  const supabase = await createServerSupabase();
  const { data: events } = await supabase
    .from("pipeline_events")
    .select("*")
    .order("ts", { ascending: false })
    .limit(100);

  return (
    <div className="space-y-2">
      <h1 className="text-2xl font-semibold">Timeline</h1>
      <ul className="space-y-2 text-sm">
        {(events || []).map((e: { id: string; ts: string; type: string; payload: unknown }) => (
          <li key={e.id} className="border border-slate-800 rounded p-2">
            <span className="text-slate-500">{e.ts}</span> — <strong>{e.type}</strong>
            <pre className="text-xs mt-1">{JSON.stringify(e.payload)}</pre>
          </li>
        ))}
      </ul>
    </div>
  );
}
