/**
 * Mental Model:
 *   The wire contract. These types mirror the FastAPI Pydantic schemas in
 *   sophia/app/schemas.py exactly. They are the single source of truth for
 *   the shape of everything that crosses the BFF boundary. If the backend
 *   schema changes, change it here too.
 */

export type Pillar = "mind" | "philosophy" | "science" | "spirit";

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type ChatRequest = {
  message: string;
  conversation_id: number | null;
  attached_file_ids: number[];
};

/** Response from POST /api/files/upload. */
export type UploadedFile = {
  id: number;
  filename: string;
  mime: string;
  chars: number;
};

/** The formats Sophia can generate for download. */
export type ExportFormat = "txt" | "md" | "pdf" | "docx";

/** Response from POST /api/images/generate. */
export type ImageGenerateOut = {
  id: number;
  filename: string;
  mime: string;
  url: string;
};

export type SourceOut = {
  text: string;
  source_file: string;
  pillar: Pillar | string;
  score: number;
};

export type ChatResponse = {
  answer: string;
  sources: SourceOut[];
  conversation_id: number;
  search_mode: string;
};

export type ConversationSummary = {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
};

export type MessageOut = {
  id: number;
  role: "user" | "sophia";
  content: string;
  /** JSON-encoded SourceOut[] for Sophia messages; null for user messages. */
  sources_json: string | null;
  created_at: string;
};

export type ConversationDetail = {
  id: number;
  title: string;
  messages: MessageOut[];
};

export type CorpusDocOut = {
  id: string;
  title: string;
  author: string;
  year: number | null;
  words: number;
  pillar: Pillar | string;
  path: string;
};

export type CorpusDocText = {
  id: string;
  title: string;
  author: string;
  pillar: Pillar | string;
  text: string;
};

export type WebResult = {
  title: string;
  url: string;
  snippet: string;
};

/* ----------------------------- SSE frames ------------------------------- */
/* The /api/chat/stream endpoint emits `event: <type>\ndata: <json>\n\n`. */

export type SseMeta = {
  search_mode: string;
  web_results: WebResult[];
  sources: SourceOut[];
  conversation_id: number;
};

export type SseToken = { text: string };

export type SseError = { message: string };

export type SseEvent =
  | { event: "meta"; data: SseMeta }
  | { event: "token"; data: SseToken }
  | { event: "done"; data: Record<string, never> }
  | { event: "error"; data: SseError };
