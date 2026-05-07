import { NextResponse } from "next/server";
import { createServerSupabase } from "@/lib/supabase/server";
import { getActiveProfileId } from "@/lib/active-profile";

export async function POST(_: Request, { params }: { params: { id: string } }) {
  const supa = await createServerSupabase();
  const {
    data: { user },
  } = await supa.auth.getUser();
  if (!user) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  const base = process.env.PROMETHEUS_API_URL;
  const secret = process.env.PIPELINE_API_SECRET;
  if (!base) return NextResponse.json({ error: "PROMETHEUS_API_URL missing" }, { status: 500 });
  if (!secret) return NextResponse.json({ error: "PIPELINE_API_SECRET missing" }, { status: 500 });

  const profileId = await getActiveProfileId();
  const resp = await fetch(`${base}/vacancies/${encodeURIComponent(params.id)}/generate/formal`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${secret}`,
      ...(profileId ? { "X-Profile-Id": profileId } : {}),
    },
    cache: "no-store",
  });
  const text = await resp.text();
  return new NextResponse(text, {
    status: resp.status,
    headers: { "content-type": resp.headers.get("content-type") || "application/json" },
  });
}

