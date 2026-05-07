import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

export async function GET() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY ?? process.env.SUPABASE_SERVICE_KEY;
  if (!key) return NextResponse.json([]);
  const supabase = createClient(url, key);
  const { data } = await supabase.from("candidate_profiles").select("id, name, profession, is_default");
  return NextResponse.json(data || []);
}

export async function POST(req: Request) {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY ?? process.env.SUPABASE_SERVICE_KEY;
  if (!key) {
    return NextResponse.json(
      { error: "Supabase service key missing (SUPABASE_SERVICE_ROLE_KEY or SUPABASE_SERVICE_KEY)" },
      { status: 500 },
    );
  }
  const body = await req.json();
  const name = String(body.name || "Новый профиль").slice(0, 120);
  const profession = String(body.profession || "Product Manager").slice(0, 200);
  const search_keywords = Array.isArray(body.search_keywords) ? body.search_keywords : [];
  const supabase = createClient(url, key);
  const { data, error } = await supabase
    .from("candidate_profiles")
    .insert({
      name,
      profession,
      search_keywords,
      is_default: false,
    })
    .select("id")
    .single();
  if (error) return NextResponse.json({ error: error.message }, { status: 400 });
  return NextResponse.json({ ok: true, id: data?.id });
}
