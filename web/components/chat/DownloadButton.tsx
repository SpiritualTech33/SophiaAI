"use client";

import { useState } from "react";
import { DownloadIcon } from "@/components/cosmic/icons";
import { clientFetch } from "@/lib/client";
import type { ExportFormat } from "@/lib/types";

const FORMATS: ExportFormat[] = ["md", "txt", "pdf", "docx"];

/**
 * Mental Model:
 *   Turns one of Sophia's answers into a file the user can keep. A small menu
 *   offers the four formats; choosing one posts the message text to the BFF,
 *   which returns the rendered bytes. We read the blob and click a temporary
 *   anchor to save it — the browser never sees the backend token.
 */
export default function DownloadButton({ content }: { content: string }) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  async function download(format: ExportFormat) {
    setBusy(true);
    try {
      const res = await clientFetch("/api/files/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content, format }),
      });
      if (!res.ok) return;

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `sophia.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      /* swallow — a failed download is non-fatal */
    } finally {
      setBusy(false);
      setOpen(false);
    }
  }

  return (
    <div className="download">
      <button
        type="button"
        className="download-trigger"
        onClick={() => setOpen((v) => !v)}
        disabled={busy}
        aria-haspopup="menu"
        aria-expanded={open}
      >
        <DownloadIcon /> Download
      </button>
      {open && (
        <ul className="download-menu" role="menu">
          {FORMATS.map((fmt) => (
            <li key={fmt} role="none">
              <button
                type="button"
                role="menuitem"
                className="download-item"
                onClick={() => download(fmt)}
              >
                {fmt.toUpperCase()}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
