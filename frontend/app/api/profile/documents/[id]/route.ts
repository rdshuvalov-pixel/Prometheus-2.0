import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import { createServerSupabase } from "@/lib/supabase/server";
import { getActiveProfileId } from "@/lib/active-profile";

function serviceSupabase() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY ?? process.env.SUPABASE_SERVICE_KEY;
  if (!key) {
    throw new Error("Supabase service key missing (SUPABASE_SERVICE_ROLE_KEY or SUPABASE_SERVICE_KEY)");
  }
  return createClient(url, key, { auth: { persistSession: false } });
}

function jsonError(code: string, status = 400) {
  return NextResponse.json({ error: code }, { status });
}

export async function DELETE(_: Request, { params }: { params: { id: string } }) {
  const supa = await createServerSupabase();
  const {
    data: { user },
  } = await supa.auth.getUser();
  if (!user) return jsonError("unauthorized", 401);

  const profileId = await getActiveProfileId();
  if (!profileId) return jsonError("no_active_profile", 400);

  const svc = serviceSupabase();
  const { data, error } = await svc
    .from("profile_documents")
    .select("id, kind, storage_path, profile_id")
    .eq("id", params.id)
    .limit(1);
  if (error) return jsonError(error.message, 400);
  const doc = data?.[0];
  if (!doc) return jsonError("not_found", 404);
  if (doc.profile_id !== profileId) return jsonError("forbidden", 403);
  if (doc.kind !== "description") return jsonError("cv_cannot_be_deleted", 405);

  if (doc.storage_path) {
    await svc.storage.from("profile-docs").remove([doc.storage_path]);
  }
  await svc.from("profile_documents").delete().eq("id", doc.id);
  return NextResponse.json({ ok: true });
}

