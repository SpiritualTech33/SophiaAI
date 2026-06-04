import { getConversations, getCorpus, requireSessionOrRedirect } from "@/lib/api";
import ChatWorkspace from "@/components/chat/ChatWorkspace";

export const metadata = { title: "Sophia — chat" };

/**
 * Mental Model:
 *   The chat page's server half. It confirms the session is still good (the
 *   proxy only checked the cookie exists; the backend may reject an expired
 *   one), then loads the two reads the workspace needs — the conversation list
 *   and the full corpus — server-side with the session cookie, and hands them
 *   to the client workspace as its initial state. No token ever reaches the
 *   browser.
 */
export default async function ChatPage() {
  await requireSessionOrRedirect();
  const [conversations, corpus] = await Promise.all([getConversations(), getCorpus()]);

  return <ChatWorkspace initialConversations={conversations} corpus={corpus} />;
}
