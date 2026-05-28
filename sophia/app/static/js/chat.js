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

  function makeSources(sources) {
    const details = document.createElement("details");
    details.className = "sources";
    const summary = document.createElement("summary");
    summary.textContent = `Sources (${sources.length})`;
    details.appendChild(summary);
    for (const s of sources) {
      const div = document.createElement("div");
      div.className = "source";
      const pillar = document.createElement("span");
      pillar.className = "pillar";
      pillar.textContent = s.pillar || "";
      const file = document.createElement("span");
      file.textContent = `${s.source_file}  ·  ${Number(s.score).toFixed(2)}`;
      const quote = document.createElement("p");
      quote.className = "msg-text";
      quote.textContent = s.text;
      div.appendChild(pillar);
      div.appendChild(file);
      div.appendChild(quote);
      details.appendChild(div);
    }
    return details;
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

    // Settle the orb back to idle after the speaking pulse.
    const orb = row.querySelector(".orb");
    setTimeout(() => { if (orb) orb.dataset.state = "idle"; }, 1500);
  }

  let typingRow = null;
  function showTyping() {
    typingRow = document.createElement("div");
    typingRow.className = "msg msg-sophia typing";
    typingRow.appendChild(makeOrb("thinking"));
    const span = document.createElement("span");
    span.textContent = "Sophia is contemplating…";
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

  function renderConversationList(conversations) {
    list.innerHTML = "";
    for (const c of conversations) {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "conversation-item";
      if (c.id === currentConversationId) btn.classList.add("active");
      btn.dataset.id = c.id;
      btn.textContent = c.title || "Untitled";
      btn.addEventListener("click", () => openConversation(c.id));
      li.appendChild(btn);
      list.appendChild(li);
    }
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

  newBtn.addEventListener("click", () => {
    currentConversationId = null;
    thread.innerHTML = "";
    thread.appendChild(emptyStateClone());
    setActiveItem(-1);
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