import type { SseMeta } from "./types";

/**
 * Mental Model:
 *   Reads a Server-Sent Events body to completion, driving the UI from each
 *   frame. The backend sends one `meta` frame first (search mode + sources +
 *   conversation id), then a run of `token` frames (answer deltas), then a
 *   single `done` or `error`. We parse frames on the "\n\n" boundary and call
 *   the matching handler. If the stream drops without an explicit terminator
 *   but we did receive content, we treat it as done; otherwise as an error.
 *   Faithful port of consumeStream() in chat.js.
 */

export type SseHandlers = {
  onMeta: (meta: SseMeta) => void;
  onToken: (delta: string) => void;
  onDone: (meta: SseMeta | null) => void;
  onError: (message: string) => void;
};

type Frame = { event: string; data: unknown };

/** Parse one raw SSE block ("event: x\ndata: {...}") into {event, data}. */
function parseFrame(block: string): Frame | null {
  let event: string | null = null;
  let data: unknown = null;
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      try {
        data = JSON.parse(line.slice(5).trim());
      } catch {
        data = null;
      }
    }
  }
  return event ? { event, data } : null;
}

export async function consumeSse(
  body: ReadableStream<Uint8Array>,
  handlers: SseHandlers,
): Promise<void> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let raw = "";
  let meta: SseMeta | null = null;
  let receivedContent = false;
  let finished = false;

  const handle = (frame: Frame) => {
    if (frame.event === "meta") {
      meta = frame.data as SseMeta;
      handlers.onMeta(meta);
    } else if (frame.event === "token") {
      const text = (frame.data as { text?: string })?.text ?? "";
      if (text) {
        receivedContent = true;
        handlers.onToken(text);
      }
    } else if (frame.event === "done") {
      finished = true;
      handlers.onDone(meta);
    } else if (frame.event === "error") {
      finished = true;
      const message =
        (frame.data as { message?: string })?.message ??
        "Sophia could not complete her answer.";
      handlers.onError(message);
    }
  };

  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    raw += decoder.decode(value, { stream: true });
    let sep: number;
    while ((sep = raw.indexOf("\n\n")) !== -1) {
      const block = raw.slice(0, sep);
      raw = raw.slice(sep + 2);
      const frame = parseFrame(block);
      if (frame) handle(frame);
    }
  }

  if (!finished) {
    if (receivedContent) handlers.onDone(meta);
    else handlers.onError("Sophia's answer was interrupted. Please try again.");
  }
}
