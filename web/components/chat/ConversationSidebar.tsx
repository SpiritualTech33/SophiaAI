"use client";

import { useMemo, useState, type KeyboardEvent } from "react";
import { motion, AnimatePresence } from "motion/react";
import GlassPanel from "@/components/cosmic/GlassPanel";
import {
  PlusIcon,
  SearchIcon,
  PencilIcon,
  TrashIcon,
  ImageIcon,
  ChevronIcon,
} from "@/components/cosmic/icons";
import { dateGroup } from "@/lib/format";
import type { ConversationSummary, ImageGenerateOut } from "@/lib/types";
import type { SidebarTab } from "./model";
import ImageGallery from "./ImageGallery";

/**
 * Mental Model:
 *   The memory shelf — now with two tabs. The "Chats" tab (default) shows
 *   past conversations, searchable and grouped by date. The "Images" tab
 *   shows a responsive grid of all images Sophia generated for the user.
 *   A tab bar at the top switches between the two views. A "Back to chats"
 *   button in the Images tab lets users return to the conversation list.
   *   Smooth tab-switching animations via AnimatePresence.
 */

const GROUPS: Array<"Today" | "Yesterday" | "Earlier"> = [
  "Today",
  "Yesterday",
  "Earlier",
];

const panelVariants = {
  hidden: { opacity: 0, x: -8 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.25, ease: [0.22, 1, 0.36, 1] as const } },
  exit: { opacity: 0, x: 8, transition: { duration: 0.18 } },
};

export default function ConversationSidebar({
  conversations,
  currentId,
  open,
  activeTab,
  onTabChange,
  onOpen,
  onNew,
  onRename,
  onDelete,
  onSignout,
  onImageClick,
}: {
  conversations: ConversationSummary[];
  currentId: number | null;
  open: boolean;
  activeTab: SidebarTab;
  onTabChange: (tab: SidebarTab) => void;
  onOpen: (id: number) => void;
  onNew: () => void;
  onRename: (id: number, title: string) => void;
  onDelete: (c: ConversationSummary) => void;
  onSignout: () => void;
  onImageClick: (image: ImageGenerateOut) => void;
}) {
  const [query, setQuery] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draft, setDraft] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q
      ? conversations.filter((c) => (c.title || "").toLowerCase().includes(q))
      : conversations;
  }, [conversations, query]);

  function beginRename(c: ConversationSummary) {
    setEditingId(c.id);
    setDraft(c.title || "");
  }

  function commitRename(c: ConversationSummary) {
    const title = draft.trim();
    setEditingId(null);
    if (title && title !== c.title) onRename(c.id, title);
  }

  function onEditKey(e: KeyboardEvent<HTMLInputElement>, c: ConversationSummary) {
    if (e.key === "Enter") {
      e.preventDefault();
      commitRename(c);
    } else if (e.key === "Escape") {
      e.preventDefault();
      setEditingId(null);
    }
  }

  return (
    <GlassPanel as="aside" id="sidebar" className={`sidebar${open ? " open" : ""}`}>
      {/* Tab bar */}
      <div className="sidebar-tab-bar" role="tablist" aria-label="Sidebar sections">
        <button
          type="button"
          role="tab"
          className={`sidebar-tab${activeTab === "conversations" ? " active" : ""}`}
          aria-selected={activeTab === "conversations"}
          onClick={() => onTabChange("conversations")}
        >
          Chats
        </button>
        <button
          type="button"
          role="tab"
          className={`sidebar-tab${activeTab === "images" ? " active" : ""}`}
          aria-selected={activeTab === "images"}
          onClick={() => onTabChange("images")}
        >
          <ImageIcon size={14} /> Images
        </button>
      </div>

      {/* Tab content with animated transitions */}
      <div className="sidebar-tab-content">
        <AnimatePresence mode="wait">
          {activeTab === "conversations" && (
            <motion.div
              key="conversations"
              className="sidebar-panel"
              variants={panelVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
            >
              <div className="sidebar-head">
                <button type="button" className="btn btn-ghost" onClick={onNew}>
                  <PlusIcon /> New conversation
                </button>
                <div className="panel-search">
                  <SearchIcon />
                  <input
                    type="search"
                    placeholder="Search conversations"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    aria-label="Search conversations"
                  />
                </div>
              </div>

              <ul className="conversation-list">
                {filtered.length === 0 ? (
                  <li className="conv-empty">
                    {query ? "No conversations found." : "No conversations yet."}
                  </li>
                ) : (
                  GROUPS.map((group) => {
                    const items = filtered.filter((c) => dateGroup(c.updated_at) === group);
                    if (items.length === 0) return null;
                    return (
                      <li key={group}>
                        <ul
                          className="conversation-list"
                          style={{ margin: 0, overflow: "visible" }}
                        >
                          <li className="conv-group">{group}</li>
                          {items.map((c) => (
                            <li key={c.id} className="conv-row">
                              {editingId === c.id ? (
                                <input
                                  className="conv-edit"
                                  autoFocus
                                  maxLength={42}
                                  value={draft}
                                  onChange={(e) => setDraft(e.target.value)}
                                  onKeyDown={(e) => onEditKey(e, c)}
                                  onBlur={() => commitRename(c)}
                                  aria-label="Conversation title"
                                />
                              ) : (
                                <>
                                  <button
                                    type="button"
                                    className={`conversation-item${c.id === currentId ? " active" : ""}`}
                                    onClick={() => onOpen(c.id)}
                                  >
                                    {c.title || "Untitled"}
                                  </button>
                                  <button
                                    type="button"
                                    className="conv-rename"
                                    aria-label="Rename conversation"
                                    title="Rename conversation"
                                    onClick={() => beginRename(c)}
                                  >
                                    <PencilIcon />
                                  </button>
                                  <button
                                    type="button"
                                    className="conv-delete"
                                    aria-label="Delete conversation"
                                    title="Delete conversation"
                                    onClick={() => onDelete(c)}
                                  >
                                    <TrashIcon />
                                  </button>
                                </>
                              )}
                            </li>
                          ))}
                        </ul>
                      </li>
                    );
                  })
                )}
              </ul>
            </motion.div>
          )}

          {activeTab === "images" && (
            <motion.div
              key="images"
              className="sidebar-panel sidebar-images-panel"
              variants={panelVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
            >
              {/* Back to chats button */}
              <button
                type="button"
                className="btn btn-ghost sidebar-back-btn"
                onClick={() => onTabChange("conversations")}
              >
                <ChevronIcon size={14} /> Back to chats
              </button>

              <ImageGallery onImageClick={onImageClick} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="sidebar-foot">
        <button type="button" className="btn btn-signout" onClick={onSignout}>
          Sign out
        </button>
      </div>
    </GlassPanel>
  );
}
