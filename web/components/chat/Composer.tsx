"use client";

import { useRef, type KeyboardEvent } from "react";
import { SendIcon } from "@/components/cosmic/icons";

/**
 * Mental Model:
 *   Where the human speaks. The textarea grows with its content up to a cap,
 *   Enter sends while Shift+Enter makes a newline, and the send button is the
 *   same gesture. It clears itself on send and stays disabled while Sophia is
 *   answering so a question can't overlap her reply.
 */
export default function Composer({
  onSend,
  disabled,
}: {
  onSend: (text: string) => void;
  disabled: boolean;
}) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  function autoGrow() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }

  function submit() {
    const el = textareaRef.current;
    if (!el) return;
    const text = el.value.trim();
    if (!text || disabled) return;
    onSend(text);
    el.value = "";
    autoGrow();
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <form
      className="composer"
      onSubmit={(e) => {
        e.preventDefault();
        submit();
      }}
    >
      <textarea
        ref={textareaRef}
        placeholder="Ask Sophia…"
        rows={1}
        onInput={autoGrow}
        onKeyDown={onKeyDown}
        aria-label="Message Sophia"
      />
      <button type="submit" className="btn-send" disabled={disabled} aria-label="Send message">
        <SendIcon />
      </button>
    </form>
  );
}
