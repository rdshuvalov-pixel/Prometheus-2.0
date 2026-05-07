import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import { createServerSupabase } from "@/lib/supabase/server";
import { getActiveProfileId } from "@/lib/active-profile";
import { extractText } from "./extract-text";

const MAX_BYTES = 5 * 1024 * 1024;

function serviceSupabase() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY!;
  return createClient(url, key, { auth: { persistSession: false } });
}

function jsonError(code: string, status = 400) {
  return NextResponse.json({ error: code }, { status });
}

type Kind = "cv" | "description";
function parseKind(v: string | null): Kind | null {
  if (v === "cv" || v === "description") return v;
  return null;
}

export async function GET() {
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
    .select("id, profile_id, kind, file_name, mime_type, byte_size, uploaded_at")
    .eq("profile_id", profileId)
    .order("uploaded_at", { ascending: false });
  if (error) return jsonError(error.message, 400);
  return NextResponse.json({ documents: data || [] });
}

export async function POST(req: Request) {
  const supa = await createServerSupabase();
  const {
    data: { user },
  } = await supa.auth.getUser();
  if (!user) return jsonError("unauthorized", 401);

  const profileId = await getActiveProfileId();
  if (!profileId) return jsonError("no_active_profile", 400);

  const form = await req.formData();
  const file = form.get("file");
  const kindRaw = form.get("kind");
  const kind = parseKind(typeof kindRaw === "string" ? kindRaw : null);
  if (!kind) return jsonError("invalid_kind", 400);
  if (!(file instanceof File)) return jsonError("file_required", 400);

  if (file.size <= 0) return jsonError("empty_file", 400);
  if (file.size > MAX_BYTES) return jsonError("file_too_large", 413);

  const bytes = await file.arrayBuffer();
  let extracted: { text: string; mimeType: string };
  try {
    extracted = await extractText(file.name, file.type, bytes);
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    if (msg === "unsupported_file_type") return jsonError("unsupported_file_type", 415);
    return jsonError("extract_failed", 500);
  }

  const svc = serviceSupabase();

  if (kind === "description") {
    const { count } = await svc
      .from("profile_documents")
      .select("*", { count: "exact", head: true })
      .eq("profile_id", profileId)
      .eq("kind", "description");
    if ((count ?? 0) >= 3) return jsonError("too_many_descriptions", 400);
  }

  // For CV: overwrite existing doc (and storage file).
  if (kind === "cv") {
    const { data: existing } = await svc
      .from("profile_documents")
      .select("id, storage_path")
      .eq("profile_id", profileId)
      .eq("kind", "cv")
      .limit(1);
    const cur = existing?.[0];
    if (cur?.storage_path) {
      await svc.storage.from("profile-docs").remove([cur.storage_path]);
      await svc.from("profile_documents").delete().eq("id", cur.id);
    }
  }

  const safeName = file.name.replace(/[^\w.\-]+/g, "_").slice(0, 120) || "document";
  const ts = Date.now();
  const storagePath = `${profileId}/${kind}/${ts}_${safeName}`;

  const upload = await svc.storage.from("profile-docs").upload(storagePath, Buffer.from(bytes), {
    contentType: extracted.mimeType || file.type || "application/octet-stream",
    upsert: false,
  });
  if (upload.error) return jsonError(`upload_failed:${upload.error.message}`, 400);

  const row = {
    profile_id: profileId,
    kind,
    file_name: file.name,
    storage_path: storagePath,
    mime_type: extracted.mimeType || file.type || null,
    byte_size: file.size,
    extracted_text: extracted.text,
  };
  const { data: inserted, error } = await svc.from("profile_documents").insert(row).select("*").limit(1);
  if (error) return jsonError(error.message, 400);

  return NextResponse.json({ document: inserted?.[0] ?? row });
}

