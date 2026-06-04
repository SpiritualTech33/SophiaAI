"use client";

import { useMemo, useState, type KeyboardEvent } from "react";
import GlassPanel from "@/components/cosmic/GlassPanel";
import { PlusIcon, SearchIcon, PencilIcon, TrashIcon } from "@/components/cosmic/icons";
import { dateGroup } from "@/lib/format";
import type { ConversationSummary } from "@/lib/types";

/**
 * Mental Model:
 *   The memory shelf. Past conversations, newest first, bucketed by Today /
 *   Yesterday / Earlier, filterable by a search box. Each row opens on click;
 *   on hover a pencil turns the title into an inline editor and a trash icon
 *   deletes it. On mobile this panel slides in over the thread (`open`).
 */

const GROUPS: Array<"Today" | "Yesterday" | "Earlier"> = ["Today", "Yesterday", "Earlier"];

export default function ConversationSidebar({
  conversations,
  currentId,
  open,
  onOpen,
  onNew,
  onRename,
  onDelete,
  onSignout,
}: {
  conversations: ConversationSummary[];
  currentId: number | null;
  open: boolean;
  onOpen: (id: number) => void;
  onNew: () => void;
  onRename: (id: number, title: string) => void;
  onDelete: (c: ConversationSummary) => void;
  onSignout: () => void;
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
                <ul className="conversation-list" style={{ margin: 0, overflow: "visible" }}>
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

      <div className="sidebar-foot">
        <button type="button" className="btn btn-signout" onClick={onSignout}>
          Sign out
        </button>
      </div>
    </GlassPanel>
  );
}
