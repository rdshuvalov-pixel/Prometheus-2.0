import Link from "next/link";
import { getActiveProfileId } from "@/lib/active-profile";
import { createServerSupabase } from "@/lib/supabase/server";

export default async function VacanciesPage({
  searchParams,
}: {
  searchParams: Record<string, string | string[] | undefined>;
}) {
  const supabase = await createServerSupabase();
  const activeProfileId = await getActiveProfileId();
  let q = supabase.from("vacancies").select("*").order("created_at", { ascending: false }).limit(50);
  if (activeProfileId) {
    q = q.eq("profile_id", activeProfileId);
  }
  const status = typeof searchParams.status === "string" ? searchParams.status : undefined;
  if (status) q = q.eq("status", status);
  const { data: rows } = await q;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Вакансии</h1>
      <ul className="space-y-2">
        {(rows || []).map((v: { id: string; company: string; role_title: string; score: number | null; status: string }) => (
          <li key={v.id}>
            <Link href={`/vacancies/${v.id}`} className="text-blue-400 hover:underline">
              {v.company} — {v.role_title}
            </Link>{" "}
            <span className="text-slate-500">
              score {v.score ?? "—"} · {v.status}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
