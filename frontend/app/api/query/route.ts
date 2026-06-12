import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const body = await request.json();
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
  const target = body?.stream ? `${backendUrl}/query/stream` : `${backendUrl}/query`;
  const response = await fetch(target, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: request.headers.get("Authorization") || ""
    },
    body: JSON.stringify({ query: body.query || "", stream: Boolean(body.stream) })
  });

  if (body?.stream) {
    return new Response(response.body, {
      status: response.status,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache"
      }
    });
  }

  const payload = await response.json();
  return NextResponse.json(payload, { status: response.status });
}
