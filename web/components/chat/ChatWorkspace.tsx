"use client";

import { useCallback, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "motion/react";
import type {
  ConversationDetail,
  ConversationSummary,
  CorpusDocOut,
  ImageGenerateOut,
  SourceOut,
} from "@/lib/types";
import { clientFetch } from "@/lib/client";
import { consumeSse } from "@/lib/sse";
import { dedupeSources } from "@/lib/format";
import { randomPhrase, type ChatMessage, type SidebarTab } from "./model";
import Wordmark from "@/components/cosmic/Wordmark";
import ConversationSidebar from "./ConversationSidebar";
import ChatThread from "./ChatThread";
import Composer from "./Composer";
import GlassPanel from "@/components/cosmic/GlassPanel";
import MindPanel from "@/components/mind/MindPanel";
import DocReader from "@/components/mind/DocReader";
import ImageLightbox from "./ImageLightbox";

/**
 * Mental Model:
 *   The brain of the chat page. Holds every piece of mutable state —
 *   conversations, messages, streaming answer, cited documents, reader,
 *   sidebar tab, and image lightbox. Hands slices down to the three panels.
 *   The sidebar now supports two tabs: "conversations" (default) and "images".
 *   The header has two toggle buttons that control which tab is active.
 */

let counter = 0;
const uid = () => `c${counter++}`;

function citedFrom(sources: SourceOut[]): string[] {
  return dedupeSources(sources).map((s) => s.source_file);
}

export default function ChatWorkspace({
  initialConversations,
  corpus,
}: {
  initialConversations: ConversationSummary[];
  corpus: CorpusDocOut[];
}) {
  const router = useRouter();

  const [conversations, setConversations] = useState(initialConversations);
  const [currentId, setCurrentId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sending, setSending] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [typingPhrase, setTypingPhrase] = useState("");
  const [citedPaths, setCitedPaths] = useState<string[]>([]);
  const [readerDoc, setReaderDoc] = useState<CorpusDocOut | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarTab, setSidebarTab] = useState<SidebarTab>("conversations");
  const [mindOpen, setMindOpen] = useState(false);
  const [lightboxImage, setLightboxImage] = useState<ImageGenerateOut | null>(null);

  const byPath = useMemo(() => {
    const map = new Map<string, CorpusDocOut>();
    for (const d of corpus) map.set(d.path, d);
    return map;
  }, [corpus]);

  const refreshConversations = useCallback(async () => {
    try {
      const res = await clientFetch("/api/conversations");
      if (res.ok) setConversations((await res.json()) as ConversationSummary[]);
    } catch {
      /* keep the current list on network error */
    }
  }, []);

  const send = useCallback(
    async (text: string, fileIds: number[] = [], imageUrls: string[] = []) => {
      if (sending) return;
      setSending(true);
      setTypingPhrase(randomPhrase());
      setThinking(true);
      setMessages((m) => [
        ...m,
        { key: uid(), role: "user", content: text, sources: [], webResults: [], searchMode: "", imageUrls },
      ]);

      const sophiaKey = uid();
      let createdBubble = false;

      try {
        const res = await clientFetch("/api/chat/stream", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: text,
            conversation_id: currentId,
            attached_file_ids: fileIds,
          }),
        });

        if (!res.ok || !res.body) {
          setThinking(false);
          setMessages((m) => [
            ...m,
            {
              key: uid(),
              role: "sophia",
              content: "Sophia could not answer just now. Please try again.",
              sources: [],
              webResults: [],
              searchMode: "",
              error: true,
            },
          ]);
          return;
        }

        await consumeSse(res.body, {
          onMeta: (meta) => {
            createdBubble = true;
            setThinking(false);
            setCitedPaths(citedFrom(meta.sources));
            setMessages((m) => [
              ...m,
              {
                key: sophiaKey,
                role: "sophia",
                content: "",
                sources: meta.sources,
                webResults: meta.web_results,
                searchMode: meta.search_mode,
                streaming: true,
              },
            ]);
          },
          onToken: (delta) => {
            setMessages((m) =>
              m.map((msg) => (msg.key === sophiaKey ? { ...msg, content: msg.content + delta } : msg)),
            );
          },
          onDone: (meta) => {
            setMessages((m) =>
              m.map((msg) =>
                msg.key === sophiaKey
                  ? {
                      ...msg,
                      streaming: false,
                      sources: meta?.sources ?? msg.sources,
                      webResults: meta?.web_results ?? msg.webResults,
                      searchMode: meta?.search_mode ?? msg.searchMode,
                    }
                  : msg,
              ),
            );
            if (meta && currentId === null && meta.conversation_id != null) {
              setCurrentId(meta.conversation_id);
            }
            void refreshConversations();
          },
          onError: (message) => {
            setThinking(false);
            setMessages((m) => [
              ...m.filter((msg) => msg.key !== sophiaKey),
              { key: uid(), role: "sophia", content: message, sources: [], webResults: [], searchMode: "", error: true },
            ]);
          },
        });
      } catch {
        setThinking(false);
        if (!createdBubble) {
          setMessages((m) => [
            ...m,
            {
              key: uid(),
              role: "sophia",
              content: "Network error reaching Sophia. Please try again.",
              sources: [],
              webResults: [],
              searchMode: "",
              error: true,
            },
          ]);
        }
      } finally {
        setSending(false);
      }
    },
    [sending, currentId, refreshConversations],
  );

  const addGeneratedImage = useCallback((image: ImageGenerateOut) => {
    setMessages((m) => [
      ...m,
      {
        key: uid(),
        role: "sophia",
        content: `![generated](file:${image.id})`,
        sources: [],
        webResults: [],
        searchMode: "",
      },
    ]);
  }, []);

  const openConversation = useCallback(async (id: number) => {
    try {
      const res = await clientFetch(`/api/conversations/${id}`);
      if (!res.ok) return;
      const detail = (await res.json()) as ConversationDetail;
      const msgs: ChatMessage[] = detail.messages.map((m) => {
        if (m.role === "user") {
          return { key: `m${m.id}`, role: "user", content: m.content, sources: [], webResults: [], searchMode: "" };
        }
        let sources: SourceOut[] = [];
        if (m.sources_json) {
          try {
            sources = JSON.parse(m.sources_json) as SourceOut[];
          } catch {
            sources = [];
          }
        }
        return { key: `m${m.id}`, role: "sophia", content: m.content, sources, webResults: [], searchMode: "" };
      });
      setCurrentId(detail.id);
      setMessages(msgs);
      const lastSophia = [...msgs].reverse().find((x) => x.role === "sophia");
      setCitedPaths(lastSophia ? citedFrom(lastSophia.sources) : []);
      setSidebarOpen(false);
    } catch {
      /* ignore */
    }
  }, []);

  const newConversation = useCallback(() => {
    setCurrentId(null);
    setMessages([]);
    setCitedPaths([]);
    setSidebarOpen(false);
  }, []);

  const renameConversation = useCallback(async (id: number, title: string) => {
    try {
      const res = await clientFetch(`/api/conversations/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
      });
      if (res.ok) {
        const updated = (await res.json()) as ConversationSummary;
        setConversations((cs) => cs.map((c) => (c.id === id ? { ...c, title: updated.title } : c)));
      }
    } catch {
      /* keep the old title */
    }
  }, []);

  const deleteConversation = useCallback(
    async (c: ConversationSummary) => {
      const label = c.title || "Untitled";
      if (!window.confirm(`Delete "${label}"? This cannot be undone.`)) return;
      try {
        const res = await clientFetch(`/api/conversations/${c.id}`, { method: "DELETE" });
        if (!res.ok && res.status !== 204) return;
        setConversations((cs) => cs.filter((x) => x.id !== c.id));
        if (c.id === currentId) {
          setCurrentId(null);
          setMessages([]);
          setCitedPaths([]);
        }
      } catch {
        /* leave the list as-is on network error */
      }
    },
    [currentId],
  );

  const signout = useCallback(async () => {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } catch {
      /* navigate regardless */
    }
    router.push("/");
    router.refresh();
  }, [router]);

  const openSourceByPath = useCallback(
    (path: string) => {
      const doc = byPath.get(path);
      if (doc) setReaderDoc(doc);
    },
    [byPath],
  );

  /**
   * Toggle the sidebar open/closed for a specific tab.
   * If the sidebar is already open on the same tab, close it.
   * If it's open on a different tab, switch to the new tab.
   */
  const toggleSidebar = useCallback(
    (tab: SidebarTab) => {
      if (sidebarOpen && sidebarTab === tab) {
        setSidebarOpen(false);
      } else {
        setSidebarTab(tab);
        setSidebarOpen(true);
      }
    },
    [sidebarOpen, sidebarTab],
  );

  return (
    <>
      <header className="site-header">
        <Wordmark />
        <div className="header-toggles">
          <motion.button
            type="button"
            className={`btn btn-ghost panel-toggle${sidebarOpen && sidebarTab === "conversations" ? " active" : ""}`}
            onClick={() => toggleSidebar("conversations")}
            aria-expanded={sidebarOpen && sidebarTab === "conversations"}
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.96 }}
          >
            Chats
          </motion.button>
          <motion.button
            type="button"
            className={`btn btn-ghost panel-toggle${sidebarOpen && sidebarTab === "images" ? " active" : ""}`}
            onClick={() => toggleSidebar("images")}
            aria-expanded={sidebarOpen && sidebarTab === "images"}
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.96 }}
          >
            Images
          </motion.button>
          <motion.button
            type="button"
            className="btn btn-ghost panel-toggle"
            onClick={() => setMindOpen((v) => !v)}
            aria-expanded={mindOpen}
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.96 }}
          >
            Mind
          </motion.button>
        </div>
      </header>

      <main className="site-main">
        <div className="chat-shell">
          <ConversationSidebar
            conversations={conversations}
            currentId={currentId}
            open={sidebarOpen}
            activeTab={sidebarTab}
            onTabChange={setSidebarTab}
            onOpen={openConversation}
            onNew={newConversation}
            onRename={renameConversation}
            onDelete={deleteConversation}
            onSignout={signout}
            onImageClick={setLightboxImage}
          />

          <GlassPanel as="section" className="conversation">
            <ChatThread
              messages={messages}
              thinking={thinking}
              typingPhrase={typingPhrase}
              byPath={byPath}
              onOpenSource={openSourceByPath}
              onExample={send}
            />
            <Composer onSend={send} onImageGenerated={addGeneratedImage} disabled={sending} />
          </GlassPanel>

          <MindPanel
            corpus={corpus}
            citedPaths={citedPaths}
            open={mindOpen}
            onOpenDoc={setReaderDoc}
          />
        </div>
      </main>

      {readerDoc ? (
        <DocReader key={readerDoc.id} doc={readerDoc} onClose={() => setReaderDoc(null)} />
      ) : null}

      <ImageLightbox image={lightboxImage} onClose={() => setLightboxImage(null)} />
    </>
  );
}
