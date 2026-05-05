import Link from "next/link";
import { getActiveProfileId } from "@/lib/active-profile";
import { createServerSupabase } from "@/lib/supabase/server";
import { CopyFormal } from "./CopyFormal";

type CoverRow = { kind: string; body: string };
type VacancyRow = {
  id: string;
  company: string;
  role_title: string;
  status: string;
  score: number | null;
  match_status: string | null;
  created_at: string;
  url: string;
  normalized_work_format: string | null;
  normalized_location: string | null;
  cover_letters: CoverRow[] | null;
};

function formatDate(iso: string) {
  try {
    return new Intl.DateTimeFormat("en-US", { dateStyle: "medium" }).format(new Date(iso));
  } catch {
    return iso;
  }
}

function formalBody(letters: CoverRow[] | null | undefined): string | null {
  if (!letters?.length) return null;
  const f = letters.find((l) => l.kind === "formal");
  return f?.body ?? null;
}

export default async function VacanciesPage({
  searchParams,
}: {
  searchParams: Record<string, string | string[] | undefined>;
}) {
  const supabase = await createServerSupabase();
  const activeProfileId = await getActiveProfileId();
  let q = supabase
    .from("vacancies")
    .select(
      "id, company, role_title, status, score, match_status, created_at, url, normalized_work_format, normalized_location, cover_letters(kind, body)",
    )
    .order("created_at", { ascending: false })
    .limit(50);
  if (activeProfileId) {
    q = q.eq("profile_id", activeProfileId);
  }
  const status = typeof searchParams.status === "string" ? searchParams.status : undefined;
  if (status) {
    q = q.eq("status", status);
  } else {
    // Default: hide "New" to reduce noise.
    q = q.neq("status", "New");
  }
  const { data: rows } = await q;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-neutral-900">Vacancies</h1>
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span className="text-neutral-700 font-medium">Filter:</span>
        {[
          { key: "", label: "All" },
          { key: "Scored", label: "Scored" },
          { key: "Rejected", label: "Rejected" },
          { key: "Applied", label: "Applied" },
          { key: "New", label: "New" },
        ].map((it) => {
          const active = (status || "") === it.key;
          const href = it.key ? `/vacancies?status=${encodeURIComponent(it.key)}` : "/vacancies";
          return (
            <Link
              key={it.label}
              href={href}
              className={[
                "px-3 py-1.5 rounded-lg border text-xs font-semibold",
                active
                  ? "bg-candy-500 text-white border-candy-500"
                  : "bg-white/80 text-neutral-700 border-neutral-200 hover:border-candy-300",
              ].join(" ")}
            >
              {it.label}
            </Link>
          );
        })}
      </div>
      <ul className="grid gap-4 sm:grid-cols-1 md:grid-cols-2">
        {(rows as VacancyRow[] | null)?.map((v) => {
          const formal = formalBody(v.cover_letters);
          return (
            <li
              key={v.id}
              className="rounded-lg border border-neutral-200 bg-white/90 shadow-sm p-4 flex flex-col gap-2"
            >
              <div>
                <Link
                  href={`/vacancies/${v.id}`}
                  className="text-lg font-semibold text-candy-800 hover:text-candy-600 hover:underline"
                >
                  {v.company} — {v.role_title}
                </Link>
                <p className="text-sm text-neutral-700 mt-1">
                  Crawled: {formatDate(v.created_at)} · {v.status} · score {v.score ?? "—"}
                  {v.match_status ? ` · ${v.match_status}` : ""}
                </p>
                <a
                  href={v.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-neutral-600 hover:text-candy-800 break-all"
                >
                  {v.url}
                </a>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {v.normalized_work_format && (
                    <span className="text-xs px-2 py-0.5 rounded border border-neutral-200 bg-neutral-100 text-neutral-800">
                      {v.normalized_work_format}
                    </span>
                  )}
                  {v.normalized_location && (
                    <span className="text-xs px-2 py-0.5 rounded border border-neutral-200 bg-neutral-100 text-neutral-800">
                      {v.normalized_location}
                    </span>
                  )}
                </div>
              </div>
              <div className="mt-auto pt-2">
                <CopyFormal body={formal} />
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
