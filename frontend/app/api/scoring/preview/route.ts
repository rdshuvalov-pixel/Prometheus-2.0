import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const api = process.env.PROMETHEUS_API_URL;
  const body = await req.json();
  if (!api) {
    return NextResponse.json(
      { error: "Задайте PROMETHEUS_API_URL (backend с /scoring/preview)", fixtures: [] },
      { status: 503 },
    );
  }
  const base = api.replace(/\/$/, "");
  const r = await fetch(`${base}/scoring/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await r.json().catch(() => ({}));
  return NextResponse.json(data, { status: r.status });
}
