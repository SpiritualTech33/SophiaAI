import type { CorpusDocOut } from "@/lib/types";
import type { ChatMessage } from "./model";
import { renderAnswer } from "@/lib/markdown";
import Orb from "@/components/cosmic/Orb";
import { ModeBadge, SourceChips, WebResults } from "./SourceChips";

/**
 * Mental Model:
 *   One turn in the dialogue. A user message is a plain right-aligned bubble.
 *   A Sophia message carries her orb (speaking while the answer streams, idle
 *   once settled), the rendered-markdown answer, and — when present — the mode
 *   badge, source chips, and web links. An errored turn is a quiet plain
 *   bubble with the failure message.
 */
export default function MessageBubble({
  message,
  byPath,
  onOpenSource,
}: {
  message: ChatMessage;
  byPath: Map<string, CorpusDocOut>;
  onOpenSource: (path: string) => void;
}) {
  if (message.role === "user") {
    return (
      <div className="msg msg-user">
        <div className="bubble">
          <p className="msg-text">{message.content}</p>
        </div>
      </div>
    );
  }

  if (message.error) {
    return (
      <div className="msg msg-sophia">
        <div className="bubble">
          <p className="msg-text">{message.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="msg msg-sophia">
      <Orb state={message.streaming ? "speaking" : "idle"} />
      <div className="bubble">
        <div className="msg-text">{renderAnswer(message.content)}</div>
        {!message.streaming && (
          <>
            <ModeBadge searchMode={message.searchMode} />
            <SourceChips sources={message.sources} byPath={byPath} onOpen={onOpenSource} />
            <WebResults results={message.webResults} />
          </>
        )}
      </div>
    </div>
  );
}
