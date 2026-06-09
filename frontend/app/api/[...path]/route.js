import { NextResponse } from "next/server";

const ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"];

function buildTargetUrl(pathSegments, request) {
  const baseUrl = process.env.API_GATEWAY_URL || "http://localhost:5000";
  const normalizedBase = baseUrl.endsWith("/") ? baseUrl.slice(0, -1) : baseUrl;
  const suffix = pathSegments.join("/");
  const url = new URL(`${normalizedBase}/${suffix}`);
  url.search = request.nextUrl.search;
  return url;
}

async function parseBody(request) {
  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  if (!hasBody) {
    return undefined;
  }

  try {
    return JSON.stringify(await request.json());
  } catch {
    return undefined;
  }
}

async function proxyRequest(request, context) {
  if (!ALLOWED_METHODS.includes(request.method)) {
    return NextResponse.json(
      {
        success: false,
        message: "Metodo nao permitido.",
      },
      { status: 405 }
    );
  }

  const targetUrl = buildTargetUrl(context.params.path, request);
  const payload = await parseBody(request);
  const authHeader = request.headers.get("authorization");

  try {
    const upstream = await fetch(targetUrl, {
      method: request.method,
      headers: {
        "Content-Type": "application/json",
        ...(authHeader ? { Authorization: authHeader } : {}),
      },
      body: payload,
      cache: "no-store",
    });

    const text = await upstream.text();
    const data = text ? JSON.parse(text) : {};
    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json(
      {
        success: false,
        message: "Falha ao comunicar com a API Gateway.",
      },
      { status: 502 }
    );
  }
}

export async function GET(request, context) {
  return proxyRequest(request, context);
}

export async function POST(request, context) {
  return proxyRequest(request, context);
}

export async function PUT(request, context) {
  return proxyRequest(request, context);
}

export async function PATCH(request, context) {
  return proxyRequest(request, context);
}

export async function DELETE(request, context) {
  return proxyRequest(request, context);
}