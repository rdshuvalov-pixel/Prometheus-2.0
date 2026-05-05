import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createServerSupabase } from "@/lib/supabase/server";

function bearerToken(authHeader: string | null): string | null {
  if (!authHeader) return null;
  const m = authHeader.match(/^\s*Bearer\s+(.+)$/i);
  return m?.[1]?.trim() ?? null;
}

export async function POST(request: Request) {
  const api = process.env.PROMETHEUS_API_URL;
  if (!api) {
    return NextResponse.json(
      { error: "Set PROMETHEUS_API_URL (backend with /pipeline/full)" },
      { status: 503 },
    );
  }

  const supabase = await createServerSupabase();
  const { data } = await supabase.auth.getUser();
  if (!data.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const secret = process.env.PIPELINE_API_SECRET?.trim();
  if (secret) {
    const token = bearerToken(request.headers.get("authorization"));
    if (token !== secret) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
  }

  const cookieStore = await cookies();
  const activeProfileId = cookieStore.get("active_profile")?.value?.trim() || "";

  const base = api.replace(/\/$/, "");
  const r = await fetch(`${base}/pipeline/full`, {
    method: "POST",
    headers: {
      ...(secret ? { Authorization: `Bearer ${secret}` } : {}),
      ...(activeProfileId ? { "X-Profile-Id": activeProfileId } : {}),
    },
  });
  const out = await r.json().catch(() => ({}));
  return NextResponse.json(out, { status: r.status });
}

