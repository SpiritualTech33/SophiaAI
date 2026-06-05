"use client";

import { useRef, useState, type ChangeEvent, type KeyboardEvent } from "react";
import { PaperclipIcon, SendIcon, CloseIcon } from "@/components/cosmic/icons";
import { clientFetch } from "@/lib/client";
import type { UploadedFile } from "@/lib/types";

const ACCEPT = ".txt,.md,.pdf,.docx";

/**
 * Mental Model:
 *   Where the human speaks — and now, hands Sophia documents. The textarea grows
 *   with its content, Enter sends while Shift+Enter makes a newline. The paperclip
 *   uploads files to the BFF; each accepted file becomes a chip above the input.
 *   On send we pass the message plus the ids of the attached files, then clear
 *   both. Upload and send stay disabled while Sophia is answering.
 */
export default function Composer({
  onSend,
  disabled,
}: {
  onSend: (text: string, fileIds: number[]) => void;
  disabled: boolean;
}) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [attached, setAttached] = useState<UploadedFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

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
    onSend(text, attached.map((f) => f.id));
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

  return (
    <div className="composer-wrap">
      {attached.length > 0 && (
        <ul className="attach-chips" aria-label="Attached files">
          {attached.map((f) => (
            <li key={f.id} className="attach-chip">
              <span className="attach-chip-name">{f.filename}</span>
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
        <button
          type="button"
          className="btn-attach"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || uploading}
          aria-label="Attach files"
          title="Attach files (txt, md, pdf, docx)"
        >
          <PaperclipIcon />
        </button>
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
    </div>
  );
}
