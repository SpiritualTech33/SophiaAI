"use client";

import { useRef, type ElementType, type MouseEvent, type ReactNode } from "react";

/**
 * Mental Model:
 *   A frosted-glass surface — the spatial-UI primitive every panel sits on.
 *   Semi-transparent void, a backdrop blur, an azure-tinted edge, and now a
 *   life of its own: a slowly-rotating "membrane" border, a gentle glow that
 *   breathes, and a pool of specular light that follows the cursor (the
 *   `--mx/--my` custom properties feed `.glass-glow` in globals.css). All of
 *   that motion is gated behind prefers-reduced-motion. Polymorphic via `as`
 *   so it can be a <section>, <aside>, <article>, etc. without extra wrappers.
 */
type GlassPanelProps = {
  as?: ElementType;
  className?: string;
  children?: ReactNode;
} & Record<string, unknown>;

export default function GlassPanel({
  as: Tag = "div",
  className,
  children,
  ...rest
}: GlassPanelProps) {
  const ref = useRef<HTMLElement | null>(null);

  function trackCursor(e: MouseEvent) {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    el.style.setProperty("--mx", `${e.clientX - rect.left}px`);
    el.style.setProperty("--my", `${e.clientY - rect.top}px`);
  }

  const classes = ["glass", "glass-alive", "glass-glow", className ?? ""]
    .filter(Boolean)
    .join(" ");

  return (
    <Tag ref={ref} className={classes} onMouseMove={trackCursor} {...rest}>
      {children}
    </Tag>
  );
}
