/**
 * Mental Model:
 *   The client's one door to the BFF. Every fetch from a Client Component goes
 *   through here so a single rule holds everywhere: if the server says 401,
 *   the session is dead — drop the user at /login. Callers handle only the
 *   happy path and real errors. (These requests carry the httpOnly cookie
 *   automatically; the client never touches the token itself.)
 */
export async function clientFetch(
  input: string,
  init?: RequestInit,
): Promise<Response> {
  const res = await fetch(input, init);
  if (res.status === 401) {
    window.location.href = "/login";
    throw new Error("Session expired");
  }
  return res;
}
