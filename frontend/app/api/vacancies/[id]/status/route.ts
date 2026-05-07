import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

export async function POST(
  req: Request,
  { params }: { params: { id: string } },
) {
  const body = await req.json();
  const nextStatus = body.status as string;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY ?? process.env.SUPABASE_SERVICE_KEY;
  if (!key) {
    return NextResponse.json(
      { error: "Supabase service key missing (SUPABASE_SERVICE_ROLE_KEY or SUPABASE_SERVICE_KEY)" },
      { status: 500 },
    );
  }
  const supabase = createClient(url, key);
  const { error } = await supabase
    .from("vacancies")
    .update({ status: nextStatus })
    .eq("id", params.id);
  if (error) return NextResponse.json({ error: error.message }, { status: 400 });
  return NextResponse.json({ ok: true });
}
