import "server-only";
import { redirect } from "next/navigation";
import { readToken } from "./auth";
import { BACKEND_URL } from "./backend";
import type {
  ConversationDetail,
  ConversationSummary,
  CorpusDocOut,
} from "./types";

/**
 * Mental Model:
 *   The server-side door to FastAPI. Every call here runs on the Next.js
 *   server, reads the httpOnly session cookie, and forwards the JWT as a
 *   Bearer header — the browser never sees the token. Server Components call
 *   the typed loaders below directly; there is no client data-fetching for
 *   reads. One swap point: SOPHIA_API_URL decides where the backend lives.
 */

const BASE = BACKEND_URL;

export function apiBase(): string {
  return BASE;
}

/** Bearer header from the session cookie, or empty when unauthenticated. */
export async function authHeader(): Promise<Record<string, string>> {
  const token = await readToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * GET a JSON resource as the logged-in user. Returns null on any non-OK
 * response (e.g. 401 expired token, 404 missing) so callers decide what a
 * failure means in their context.
 */
async function apiGet<T>(path: string): Promise<T | null> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { ...(await authHeader()) },
    cache: "no-store",
  });
  if (!res.ok) return null;
  return (await res.json()) as T;
}

/* ----------------------------- Typed loaders ---------------------------- */

/** All of the user's conversations, newest first. Empty list on failure. */
export async function getConversations(): Promise<ConversationSummary[]> {
  return (await apiGet<ConversationSummary[]>("/api/conversations")) ?? [];
}

/** One conversation with its messages, or null if it isn't the user's. */
export async function getConversation(id: number): Promise<ConversationDetail | null> {
  return apiGet<ConversationDetail>(`/api/conversations/${id}`);
}

/** The full corpus metadata for Sophia's Mind. Empty list on failure. */
export async function getCorpus(): Promise<CorpusDocOut[]> {
  return (await apiGet<CorpusDocOut[]>("/api/corpus")) ?? [];
}

/**
 * Guard a Server Component: if the session is missing or rejected by the
 * backend, send the user to /login. Use when a page cannot render without a
 * valid session even though the proxy already checked cookie presence (the
 * cookie may exist but be expired).
 */
export async function requireSessionOrRedirect(): Promise<void> {
  const res = await fetch(`${BASE}/api/conversations`, {
    headers: { ...(await authHeader()) },
    cache: "no-store",
  });
  if (res.status === 401) redirect("/login");
}
