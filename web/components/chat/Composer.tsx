"use client";

import { useRef, useState, type ChangeEvent, type KeyboardEvent } from "react";
import { motion } from "motion/react";
import { PaperclipIcon, SendIcon, CloseIcon, ImageIcon } from "@/components/cosmic/icons";
import { clientFetch } from "@/lib/client";
import type { ImageGenerateOut, UploadedFile } from "@/lib/types";

const ACCEPT = ".txt,.md,.pdf,.docx,image/jpeg,image/png,image/webp,image/gif";
const IMAGE_MIME_PREFIX = "image/";

/**
 * Mental Model:
 *   Where the human speaks — and now, hands Sophia documents and images. The
 *   textarea grows with its content, Enter sends while Shift+Enter makes a
 *   newline. The paperclip uploads files to the BFF; each accepted file becomes
 *   a chip above the input — images render as a thumbnail, other files as a
 *   filename chip. The picture button opens an inline prompt that asks Sophia
 *   to generate an image via the BFF, then hands the result to onImageGenerated
 *   so it appears as a Sophia message. On send we pass the message plus the ids
 *   of the attached files, then clear both. Upload and send stay disabled while
 *   Sophia is answering.
 */
export default function Composer({
  onSend,
  onImageGenerated,
  disabled,
}: {
  onSend: (text: string, fileIds: number[], imageUrls: string[]) => void;
  onImageGenerated: (image: ImageGenerateOut) => void;
  disabled: boolean;
}) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [attached, setAttached] = useState<UploadedFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [generateOpen, setGenerateOpen] = useState(false);
  const [generatePrompt, setGeneratePrompt] = useState("");
  const [generateError, setGenerateError] = useState<string | null>(null);

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
    const imageUrls = attached
      .filter((f) => f.mime.startsWith(IMAGE_MIME_PREFIX))
      .map((f) => `/api/files/${f.id}/raw`);
    onSend(text, attached.map((f) => f.id), imageUrls);
    el.value = "";
    setAttached([]);
    autoGrow();
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  async function onFilesPicked(e: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    e.target.value = ""; // allow re-picking the same file later
    if (files.length === 0) return;

    setUploading(true);
    setUploadError(null);
    try {
      for (const file of files) {
        const form = new FormData();
        form.append("file", file);
        const res = await clientFetch("/api/files/upload", { method: "POST", body: form });
        if (!res.ok) {
          const detail = await res.json().catch(() => null);
          setUploadError(detail?.detail ?? `Could not upload ${file.name}.`);
          continue;
        }
        const uploaded = (await res.json()) as UploadedFile;
        setAttached((prev) => [...prev, uploaded]);
      }
    } catch {
      setUploadError("Network error during upload. Please try again.");
    } finally {
      setUploading(false);
    }
  }

  function removeAttachment(id: number) {
    setAttached((prev) => prev.filter((f) => f.id !== id));
  }

  async function submitGeneratePrompt() {
    const prompt = generatePrompt.trim();
    if (!prompt || generating) return;

    setGenerating(true);
    setGenerateError(null);
    try {
      const res = await clientFetch("/api/images/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => null);
        setGenerateError(detail?.detail ?? "Sophia could not create that image.");
        return;
      }
      const image = (await res.json()) as ImageGenerateOut;
      onImageGenerated(image);
      setGeneratePrompt("");
      setGenerateOpen(false);
    } catch {
      setGenerateError("Network error during image generation. Please try again.");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="composer-wrap">
      {attached.length > 0 && (
        <ul className="attach-chips" aria-label="Attached files">
          {attached.map((f) => (
            <li key={f.id} className="attach-chip">
              {f.mime.startsWith(IMAGE_MIME_PREFIX) ? (
                <img className="attach-chip-thumb" src={`/api/files/${f.id}/raw`} alt={f.filename} />
              ) : (
                <span className="attach-chip-name">{f.filename}</span>
              )}
              <button
                type="button"
                className="attach-chip-remove"
                onClick={() => removeAttachment(f.id)}
                aria-label={`Remove ${f.filename}`}
              >
                <CloseIcon size={12} />
              </button>
            </li>
          ))}
        </ul>
      )}

      {uploadError && <p className="attach-error">{uploadError}</p>}

      {generateOpen && (
        <form
          className="generate-prompt"
          onSubmit={(e) => {
            e.preventDefault();
            void submitGeneratePrompt();
          }}
        >
          <input
            type="text"
            value={generatePrompt}
            onChange={(e) => setGeneratePrompt(e.target.value)}
            placeholder="Describe the image Sophia should create…"
            aria-label="Image prompt"
            disabled={generating}
            autoFocus
          />
          <button type="submit" className="btn btn-ghost" disabled={generating || !generatePrompt.trim()}>
            {generating ? "Creating…" : "Create"}
          </button>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => {
              setGenerateOpen(false);
              setGenerateError(null);
            }}
            disabled={generating}
          >
            Cancel
          </button>
        </form>
      )}

      {generateError && <p className="attach-error">{generateError}</p>}

      <form
        className="composer"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={ACCEPT}
          className="attach-input"
          onChange={onFilesPicked}
          aria-hidden
          tabIndex={-1}
        />
        <motion.button
          type="button"
          className="btn-attach"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || uploading}
          aria-label="Attach files"
          title="Attach files (txt, md, pdf, docx)"
          whileHover={disabled || uploading ? undefined : { scale: 1.08 }}
          whileTap={disabled || uploading ? undefined : { scale: 0.92 }}
        >
          <PaperclipIcon />
        </motion.button>
        <motion.button
          type="button"
          className="btn-attach"
          onClick={() => setGenerateOpen((v) => !v)}
          disabled={disabled}
          aria-label="Generate image"
          aria-expanded={generateOpen}
          title="Ask Sophia to generate an image"
          whileHover={disabled ? undefined : { scale: 1.08 }}
          whileTap={disabled ? undefined : { scale: 0.92 }}
        >
          <ImageIcon />
        </motion.button>
        <textarea
          ref={textareaRef}
          placeholder="Ask Sophia…"
          rows={1}
          onInput={autoGrow}
          onKeyDown={onKeyDown}
          aria-label="Message Sophia"
        />
        <motion.button
          type="submit"
          className="btn-send"
          disabled={disabled}
          aria-label="Send message"
          whileHover={disabled ? undefined : { scale: 1.06 }}
          whileTap={disabled ? undefined : { scale: 0.92 }}
        >
          <SendIcon />
        </motion.button>
      </form>
    </div>
  );
}
