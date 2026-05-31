/* =========================================================================
   chat.js — the cosmic chat portal behavior.

   Responsibilities:
     - guard the page (requireAuth)
     - load + render the conversation list
     - send a message and render Sophia's answer (orb states + typing)
     - load a past conversation
     - start a new conversation, sign out

   Security: all user/server text is rendered via textContent and
   createElement. We never build HTML from strings, so message content
   cannot inject markup (XSS-safe).
   ========================================================================= */

import { authFetch, requireAuth, clearToken } from "/static/js/cosmos.js";

if (requireAuth()) {
  initChat();
}

function initChat() {
  const thread = document.getElementById("thread");
  const emptyState = document.getElementById("empty-state");
  const composer = document.getElementById("composer");
  const textarea = document.getElementById("message");
  const sendBtn = document.getElementById("send");
  const list = document.getElementById("conversation-list");
  const newBtn = document.getElementById("new-conversation");
  const signoutBtn = document.getElementById("signout");
  const sidebar = document.getElementById("sidebar");
  const menuToggle = document.getElementById("menu-toggle");
  const convSearch = document.getElementById("conversation-search");

  let currentConversationId = null;
  let sending = false;

  /* ----------------------------- Rendering ----------------------------- */

  function clearEmptyState() {
    if (emptyState && emptyState.parentNode) emptyState.remove();
  }

  function scrollToBottom() {
    thread.scrollTop = thread.scrollHeight;
  }

  function makeOrb(state) {
    const orb = document.createElement("span");
    orb.className = "orb";
    orb.dataset.state = state;
    orb.setAttribute("aria-hidden", "true");
    return orb;
  }

  function appendUserMessage(text) {
    clearEmptyState();
    const row = document.createElement("div");
    row.className = "msg msg-user";
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    const p = document.createElement("p");
    p.className = "msg-text";
    p.textContent = text;
    bubble.appendChild(p);
    row.appendChild(bubble);
    thread.appendChild(row);
    scrollToBottom();
  }

  const ICON_BOOK =
    '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20M4 4.5A2.5 2.5 0 0 1 6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5z"/>';
  const ICON_GLOBE =
    '<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20"/>';

  function makeBadge(searchMode) {
    const badge = document.createElement("span");
    badge.className = "badge";
    const isWeb = /web/i.test(searchMode || "");
    const svgNS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "2");
    svg.innerHTML = isWeb ? ICON_GLOBE : ICON_BOOK; // static icon strings, not user data
    const label = document.createElement("span");
    label.textContent = searchMode || "corpus";
    badge.appendChild(svg);
    badge.appendChild(label);
    return badge;
  }

  // Collapse a source list to one chip per distinct document, keeping the
  // first occurrence (highest score) of each file.
  function dedupeSources(sources) {
    const seen = new Map();
    for (const s of sources) {
      if (!seen.has(s.source_file)) seen.set(s.source_file, s);
    }
    return [...seen.values()];
  }

  function prettyTitle(path) {
    const corpus = window.__corpusByPath;
    if (corpus && corpus.has(path)) return corpus.get(path).title;
    const file = path.split("/").pop().replace(/\.md$/, "");
    return file.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }

  // Source chips: clicking one opens that document in Sophia's Mind panel.
  function makeSources(sources) {
    const unique = dedupeSources(sources);
    const wrap = document.createElement("div");
    wrap.className = "src-cite";
    const label = document.createElement("div");
    label.className = "src-label";
    label.textContent = "Drawn from Sophia's mind";
    wrap.appendChild(label);

    const row = document.createElement("div");
    row.className = "src-row";
    for (const s of unique) {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "src-chip";
      if (s.pillar) chip.style.setProperty("--p", `var(--pillar-${s.pillar})`);
      const dot = document.createElement("span");
      dot.className = "dot";
      const ct = document.createElement("span");
      ct.className = "ct";
      ct.textContent = prettyTitle(s.source_file);
      chip.append(dot, ct);
      chip.addEventListener("click", () =>
        window.dispatchEvent(
          new CustomEvent("sophia:open", { detail: { path: s.source_file } })
        )
      );
      row.appendChild(chip);
    }
    wrap.appendChild(row);
    return wrap;
  }

  // Tell the Mind panel which documents this answer drew from.
  function emitCitations(sources) {
    const paths = dedupeSources(sources || []).map((s) => s.source_file);
    window.dispatchEvent(new CustomEvent("sophia:cite", { detail: { paths } }));
  }

  function appendSophiaMessage({ answer, sources, search_mode }) {
    clearEmptyState();
    const row = document.createElement("div");
    row.className = "msg msg-sophia";
    row.appendChild(makeOrb("speaking"));

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    const p = document.createElement("p");
    p.className = "msg-text";
    p.textContent = answer;
    bubble.appendChild(p);

    bubble.appendChild(makeBadge(search_mode));
    if (sources && sources.length) bubble.appendChild(makeSources(sources));

    row.appendChild(bubble);
    thread.appendChild(row);
    scrollToBottom();

    // Light up the cited documents in Sophia's Mind.
    emitCitations(sources);

    // Settle the orb back to idle after the speaking pulse.
    const orb = row.querySelector(".orb");
    setTimeout(() => { if (orb) orb.dataset.state = "idle"; }, 1500);
  }

  // Loading phrases shown while the LLM generates. One is picked at random
  // per query so the wait feels alive instead of repeating the same line.
  const CONTEMPLATION_PHRASES = [
    "Sophia is philosophizing…",
    "Sophia is connecting with higher dimensions…",
    "Sophia is thinking…",
    "Sophia is symbiotizing…",
    "Sophia is contemplating…",
    "Sophia is reasoning…",
    "Sophia is connecting with Nous…",
  ];

  let typingRow = null;
  function showTyping() {
    typingRow = document.createElement("div");
    typingRow.className = "msg msg-sophia typing";
    typingRow.appendChild(makeOrb("thinking"));
    const span = document.createElement("span");
    const index = Math.floor(Math.random() * CONTEMPLATION_PHRASES.length);
    span.textContent = CONTEMPLATION_PHRASES[index];
    typingRow.appendChild(span);
    thread.appendChild(typingRow);
    scrollToBottom();
  }
  function hideTyping() {
    if (typingRow && typingRow.parentNode) typingRow.remove();
    typingRow = null;
  }

  function showErrorBubble(message) {
    const row = document.createElement("div");
    row.className = "msg msg-sophia";
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    const p = document.createElement("p");
    p.className = "msg-text";
    p.textContent = message;
    bubble.appendChild(p);
    row.appendChild(bubble);
    thread.appendChild(row);
    scrollToBottom();
  }

  /* ----------------------------- Conversations ------------------------- */

  async function loadConversations() {
    try {
      const res = await authFetch("/api/conversations");
      if (!res.ok) return;
      const conversations = await res.json();
      renderConversationList(conversations);
    } catch (_) { /* network handled elsewhere */ }
  }

  let allConversations = [];

  function renderConversationList(conversations) {
    allConversations = conversations;
    renderFilteredConversations();
  }

  // Bucket a conversation by its last-activity date.
  function dateGroup(iso) {
    const then = new Date(iso);
    const today = new Date();
    const startOfToday = new Date(today.getFullYear(), today.getMonth(), today.getDate());
    const startOfThen = new Date(then.getFullYear(), then.getMonth(), then.getDate());
    const dayMs = 86400000;
    const diff = Math.round((startOfToday - startOfThen) / dayMs);
    if (diff <= 0) return "Today";
    if (diff === 1) return "Yesterday";
    return "Earlier";
  }

  function renderFilteredConversations() {
    const q = (convSearch ? convSearch.value : "").trim().toLowerCase();
    const filtered = q
      ? allConversations.filter((c) => (c.title || "").toLowerCase().includes(q))
      : allConversations;

    list.innerHTML = "";
    if (filtered.length === 0) {
      const empty = document.createElement("li");
      empty.className = "conv-empty";
      empty.textContent = q ? "No conversations found." : "No conversations yet.";
      list.appendChild(empty);
      return;
    }

    for (const group of ["Today", "Yesterday", "Earlier"]) {
      const items = filtered.filter((c) => dateGroup(c.updated_at) === group);
      if (items.length === 0) continue;

      const header = document.createElement("li");
      header.className = "conv-group";
      header.textContent = group;
      list.appendChild(header);

      for (const c of items) {
        list.appendChild(makeConversationRow(c));
      }
    }
  }

  // One conversation row: a title button that opens it, plus a pencil that
  // turns the title into an inline editor.
  function makeConversationRow(c) {
    const li = document.createElement("li");
    li.className = "conv-row";

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "conversation-item";
    if (c.id === currentConversationId) btn.classList.add("active");
    btn.dataset.id = c.id;
    btn.textContent = c.title || "Untitled";
    btn.addEventListener("click", () => openConversation(c.id));

    const rename = document.createElement("button");
    rename.type = "button";
    rename.className = "conv-rename";
    rename.title = "Rename conversation";
    rename.setAttribute("aria-label", "Rename conversation");
    rename.innerHTML =
      '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z"/></svg>';
    rename.addEventListener("click", (e) => {
      e.stopPropagation();
      beginRename(li, c);
    });

    const del = document.createElement("button");
    del.type = "button";
    del.className = "conv-delete";
    del.title = "Delete conversation";
    del.setAttribute("aria-label", "Delete conversation");
    del.innerHTML =
      '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6h18"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg>';
    del.addEventListener("click", (e) => {
      e.stopPropagation();
      deleteConversation(c);
    });

    li.append(btn, rename, del);
    return li;
  }

  // Confirm, then delete a conversation. If it was the open one, reset the
  // view to the empty "new conversation" state.
  async function deleteConversation(c) {
    const label = c.title || "Untitled";
    if (!window.confirm(`Delete "${label}"? This cannot be undone.`)) return;
    try {
      const res = await authFetch(`/api/conversations/${c.id}`, { method: "DELETE" });
      if (!res.ok) return;
      allConversations = allConversations.filter((conv) => conv.id !== c.id);
      if (c.id === currentConversationId) {
        currentConversationId = null;
        thread.innerHTML = "";
        thread.appendChild(emptyStateClone());
        emitCitations([]); // clear the Mind panel highlight
      }
      renderFilteredConversations();
    } catch (_) { /* leave the list as-is on network error */ }
  }

  // Swap a row for an input; Enter or blur saves, Escape cancels.
  function beginRename(li, c) {
    const input = document.createElement("input");
    input.type = "text";
    input.className = "conv-edit";
    input.maxLength = 42;
    input.value = c.title || "";
    li.replaceChildren(input);
    input.focus();
    input.select();

    let done = false;
    const cancel = () => {
      if (done) return;
      done = true;
      renderFilteredConversations();
    };
    const save = async () => {
      if (done) return;
      const title = input.value.trim();
      if (!title || title === c.title) return cancel();
      done = true;
      await renameConversation(c.id, title);
    };

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") { e.preventDefault(); save(); }
      else if (e.key === "Escape") { e.preventDefault(); cancel(); }
    });
    input.addEventListener("blur", save);
  }

  async function renameConversation(id, title) {
    try {
      const res = await authFetch(`/api/conversations/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ title }),
      });
      if (res.ok) {
        const updated = await res.json();
        const target = allConversations.find((c) => c.id === id);
        if (target) target.title = updated.title;
      }
    } catch (_) { /* leave the old title in place */ }
    renderFilteredConversations();
  }

  function setActiveItem(id) {
    for (const btn of list.querySelectorAll(".conversation-item")) {
      btn.classList.toggle("active", Number(btn.dataset.id) === id);
    }
  }

  async function openConversation(id) {
    try {
      const res = await authFetch(`/api/conversations/${id}`);
      if (!res.ok) return;
      const detail = await res.json();
      currentConversationId = detail.id;
      setActiveItem(id);
      thread.innerHTML = "";
      emitCitations([]); // reset; the last answer below re-lights the panel
      for (const m of detail.messages) {
        if (m.role === "user") {
          appendUserMessage(m.content);
        } else {
          let sources = [];
          if (m.sources_json) {
            try { sources = JSON.parse(m.sources_json); } catch (_) { sources = []; }
          }
          appendSophiaMessage({ answer: m.content, sources, search_mode: "" });
        }
      }
      closeSidebarMobile();
    } catch (_) { /* ignore */ }
  }

  /* ----------------------------- Send flow ----------------------------- */

  async function send(text) {
    if (sending) return;
    sending = true;
    sendBtn.disabled = true;
    textarea.value = "";
    autoGrow();

    appendUserMessage(text);
    showTyping();

    try {
      const res = await authFetch("/api/chat", {
        method: "POST",
        body: JSON.stringify({ message: text, conversation_id: currentConversationId }),
      });
      hideTyping();

      if (!res.ok) {
        showErrorBubble("Sophia could not answer just now. Please try again.");
        return;
      }

      const data = await res.json();
      appendSophiaMessage(data);

      const isNew = currentConversationId === null;
      currentConversationId = data.conversation_id;
      if (isNew) {
        await loadConversations();
        setActiveItem(currentConversationId);
      }
    } catch (_) {
      hideTyping();
      showErrorBubble("Network error reaching Sophia. Please try again.");
    } finally {
      sending = false;
      sendBtn.disabled = false;
      textarea.focus();
    }
  }

  /* ----------------------------- Composer UX --------------------------- */

  function autoGrow() {
    textarea.style.height = "auto";
    textarea.style.height = Math.min(textarea.scrollHeight, 160) + "px";
  }

  textarea.addEventListener("input", autoGrow);
  textarea.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      composer.requestSubmit();
    }
  });

  composer.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = textarea.value.trim();
    if (text) send(text);
  });

  for (const chip of document.querySelectorAll(".chip")) {
    chip.addEventListener("click", () => send(chip.textContent.trim()));
  }

  /* ----------------------------- Sidebar / nav ------------------------- */

  if (convSearch) {
    convSearch.addEventListener("input", renderFilteredConversations);
  }

  newBtn.addEventListener("click", () => {
    currentConversationId = null;
    thread.innerHTML = "";
    thread.appendChild(emptyStateClone());
    setActiveItem(-1);
    emitCitations([]); // clear the Mind panel highlight
    closeSidebarMobile();
    textarea.focus();
  });

  // Keep a pristine copy of the empty state to restore on "new conversation".
  const emptyStateTemplate = emptyState.cloneNode(true);
  function emptyStateClone() {
    const clone = emptyStateTemplate.cloneNode(true);
    clone.querySelectorAll(".chip").forEach((chip) =>
      chip.addEventListener("click", () => send(chip.textContent.trim()))
    );
    return clone;
  }

  signoutBtn.addEventListener("click", () => {
    clearToken();
    window.location.replace("/");
  });

  function closeSidebarMobile() {
    sidebar.classList.remove("open");
    if (menuToggle) menuToggle.setAttribute("aria-expanded", "false");
  }
  if (menuToggle) {
    menuToggle.addEventListener("click", () => {
      const open = sidebar.classList.toggle("open");
      menuToggle.setAttribute("aria-expanded", String(open));
    });
  }

  /* ----------------------------- Boot ---------------------------------- */
  loadConversations();
  textarea.focus();
}