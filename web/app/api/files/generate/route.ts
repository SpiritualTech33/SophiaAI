import { forward } from "@/lib/backend";

/**
 * Mental Model:
 *   The download door of the BFF. The browser posts { content, format }; we
 *   relay it to FastAPI, which renders the file and answers with binary bytes
 *   plus a Content-Disposition. We must relay those bytes verbatim — not via
 *   text() — or a PDF/DOCX would be corrupted. We preserve the content-type and
 *   the attachment filename so the browser saves it correctly.
 */
export const runtime = "nodejs";

export async function POST(request: Request) {
  const body = await request.text();

  const res = await forward("/api/files/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });

  if (!res.ok) {
    // Error bodies are JSON; relay them as-is so the client can read the detail.
    return new Response(await res.text(), {
      status: res.status,
      headers: { "Content-Type": res.headers.get("content-type") ?? "application/json" },
    });
  }

  const bytes = await res.arrayBuffer();
  return new Response(bytes, {
    status: 200,
    headers: {
      "Content-Type": res.headers.get("content-type") ?? "application/octet-stream",
      "Content-Disposition": res.headers.get("content-disposition") ?? "attachment",
    },
  });
}
