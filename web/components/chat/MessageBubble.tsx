"use client";

import type { ReactNode } from "react";
import { motion, useReducedMotion } from "motion/react";
import type { CorpusDocOut } from "@/lib/types";
import type { ChatMessage } from "./model";
import { renderAnswer } from "@/lib/markdown";
import Orb from "@/components/cosmic/Orb";
import { ModeBadge, SourceChips, WebResults } from "./SourceChips";
import DownloadButton from "./DownloadButton";

/**
 * Mental Model:
 *   One turn in the dialogue. A user message is a plain right-aligned bubble.
 *   A Sophia message carries her orb (speaking while the answer streams, idle
 *   once settled), the rendered-markdown answer, and — when present — the mode
 *   badge, source chips, and web links. An errored turn is a quiet plain
 *   bubble with the failure message. Each turn springs into view on mount
 *   (Motion), with a small index-based delay so a freshly-loaded history
 *   cascades in rather than snapping. Reduced-motion renders it instantly.
 */
export default function MessageBubble({
  message,
  byPath,
  onOpenSource,
  index = 0,
}: {
  message: ChatMessage;
  byPath: Map<string, CorpusDocOut>;
  onOpenSource: (path: string) => void;
  index?: number;
}) {
  const reduce = useReducedMotion();
  const enter = reduce
    ? {}
    : {
        initial: { opacity: 0, y: 14 },
        animate: { opacity: 1, y: 0 },
        transition: {
          type: "spring" as const,
          stiffness: 320,
          damping: 30,
          delay: Math.min(index * 0.04, 0.24),
        },
      };

  let className = "msg ";
  let inner: ReactNode;

  if (message.role === "user") {
    className += "msg-user";
    inner = (
      <div className="bubble">
        <p className="msg-text">{message.content}</p>
      </div>
    );
  } else if (message.error) {
    className += "msg-sophia";
    inner = (
      <div className="bubble">
        <p className="msg-text">{message.content}</p>
      </div>
    );
  } else {
    className += "msg-sophia";
    inner = (
      <>
        <Orb state={message.streaming ? "speaking" : "idle"} />
        <div className="bubble">
          <div className="msg-text">{renderAnswer(message.content)}</div>
          {!message.streaming && (
            <>
              <ModeBadge searchMode={message.searchMode} />
              <SourceChips sources={message.sources} byPath={byPath} onOpen={onOpenSource} />
              <WebResults results={message.webResults} />
              {message.content.trim() && <DownloadButton content={message.content} />}
            </>
          )}
        </div>
      </>
    );
  }

  return (
    <motion.div className={className} {...enter}>
      {inner}
    </motion.div>
  );
}
