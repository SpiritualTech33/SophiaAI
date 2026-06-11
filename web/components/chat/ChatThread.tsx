"use client";

import { useEffect, useRef } from "react";
import type { CorpusDocOut } from "@/lib/types";
import type { ChatMessage } from "./model";
import Orb from "@/components/cosmic/Orb";
import MessageBubble from "./MessageBubble";

/**
 * Mental Model:
 *   The dialogue river. With no messages it shows an invitation — the hero orb
 *   and a few example questions. Otherwise it lists the turns and, while Sophia
 *   is gathering her thoughts (before the first token), a typing line with a
 *   thinking orb. It keeps itself scrolled to the newest content.
 */

const EXAMPLES = [
  "What did the Stoics mean by living according to nature?",
  "How does Jung describe the shadow?",
  "What is the Tao that cannot be named?",
];

export default function ChatThread({
  messages,
  thinking,
  typingPhrase,
  byPath,
  onOpenSource,
  onExample,
}: {
  messages: ChatMessage[];
  thinking: boolean;
  typingPhrase: string;
  byPath: Map<string, CorpusDocOut>;
  onOpenSource: (path: string) => void;
  onExample: (text: string) => void;
}) {
  const threadRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const el = threadRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, thinking]);

  const empty = messages.length === 0 && !thinking;

  return (
    <div className="thread" ref={threadRef}>
      {empty ? (
        <div className="empty-state">
          <Orb large state="idle" />
          <p>Ask Sophia anything. She answers from the wisdom of the ages.</p>
          <div className="example-chips">
            {EXAMPLES.map((q) => (
              <button key={q} type="button" className="chip" onClick={() => onExample(q)}>
                {q}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <>
          {messages.map((m, i) => (
            <MessageBubble key={m.key} index={i} message={m} byPath={byPath} onOpenSource={onOpenSource} />
          ))}
          {thinking && (
            <div className="msg msg-sophia typing">
              <Orb state="thinking" />
              <span>{typingPhrase}</span>
            </div>
          )}
        </>
      )}
    </div>
  );
}
