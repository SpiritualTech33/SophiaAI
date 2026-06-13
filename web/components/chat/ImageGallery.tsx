"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { clientFetch } from "@/lib/client";
import type { ImageGenerateOut } from "@/lib/types";

/**
 * Mental Model:
 *   The image gallery grid for the sidebar's Images tab. Fetches all
 *   generated images for the current user from the BFF and renders them
 *   as a responsive thumbnail grid with staggered entrance animations.
 *   Clicking a thumbnail opens the lightbox.
 */

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.06, delayChildren: 0.1 },
  },
};

const cardVariants = {
  hidden: { opacity: 0, scale: 0.8, y: 12 },
  show: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: { type: "spring" as const, stiffness: 300, damping: 22 },
  },
};

export default function ImageGallery({
  onImageClick,
}: {
  onImageClick: (image: ImageGenerateOut) => void;
}) {
  const [images, setImages] = useState<ImageGenerateOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchImages() {
      setLoading(true);
      setError(null);
      try {
        const res = await clientFetch("/api/images");
        if (!res.ok) {
          setError("Could not load images.");
          return;
        }
        const data = (await res.json()) as ImageGenerateOut[];
        if (!cancelled) setImages(data);
      } catch {
        if (!cancelled) setError("Network error loading images.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchImages();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="image-gallery">
        {Array.from({ length: 6 }).map((_, i) => (
          <motion.div
            key={i}
            className="image-card image-card-skeleton"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: i * 0.08 }}
          />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <motion.p
        className="image-gallery-error"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
      >
        {error}
      </motion.p>
    );
  }

  if (images.length === 0) {
    return (
      <motion.p
        className="image-gallery-empty"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      >
        No images yet. Ask Sophia to generate one!
      </motion.p>
    );
  }

  return (
    <motion.div
      className="image-gallery"
      variants={containerVariants}
      initial="hidden"
      animate="show"
    >
      <AnimatePresence>
        {images.map((image) => (
          <motion.button
            key={image.id}
            type="button"
            className="image-card"
            variants={cardVariants}
            onClick={() => onImageClick(image)}
            aria-label={`View ${image.filename}`}
            title={image.filename}
            whileHover={{
              scale: 1.08,
              zIndex: 2,
              transition: { type: "spring", stiffness: 400, damping: 18 },
            }}
            whileTap={{ scale: 0.94 }}
          >
            <motion.img
              src={image.url}
              alt={image.filename}
              loading="lazy"
              className="image-card-img"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            />
          </motion.button>
        ))}
      </AnimatePresence>
    </motion.div>
  );
}
