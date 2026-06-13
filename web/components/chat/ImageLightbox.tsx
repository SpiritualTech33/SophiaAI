"use client";

import { useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { CloseIcon } from "@/components/cosmic/icons";
import type { ImageGenerateOut } from "@/lib/types";

/**
 * Mental Model:
 *   Full-screen lightbox overlay for viewing a generated image at full size.
 *   Renders above everything (z-[200]) so it's never hidden behind the sidebar
 *   or chat. Smooth spring entrance/exit animations. Escape key, click-outside,
 *   and close button all dismiss.
 */

export default function ImageLightbox({
  image,
  onClose,
}: {
  image: ImageGenerateOut | null;
  onClose: () => void;
}) {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    },
    [onClose],
  );

  useEffect(() => {
    if (!image) return;
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [image, handleKeyDown]);

  return (
    <AnimatePresence>
      {image && (
        <motion.div
          className="lightbox-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          onClick={onClose}
          role="dialog"
          aria-modal="true"
          aria-label={`Full-size view of ${image.filename}`}
        >
          <motion.div
            className="lightbox-content"
            initial={{ opacity: 0, scale: 0.88, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.92, y: 12 }}
            transition={{ type: "spring" as const, stiffness: 350, damping: 28 }}
            onClick={(e) => e.stopPropagation()}
          >
            <motion.button
              type="button"
              className="lightbox-close"
              onClick={onClose}
              aria-label="Close image viewer"
              whileHover={{ scale: 1.15, backgroundColor: "var(--surface-2)" }}
              whileTap={{ scale: 0.9 }}
            >
              <CloseIcon size={20} />
            </motion.button>
            <motion.img
              src={image.url}
              alt={image.filename}
              className="lightbox-img"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1, duration: 0.3 }}
            />
            <motion.p
              className="lightbox-filename"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.3 }}
            >
              {image.filename}
            </motion.p>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
