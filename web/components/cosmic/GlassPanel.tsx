import type { ElementType, ReactNode } from "react";

/**
 * Mental Model:
 *   A frosted-glass surface — the spatial-UI primitive every panel sits on.
 *   Semi-transparent void, a modest backdrop blur, and an azure-tinted edge
 *   lit along the top (see `.glass` in globals.css). Polymorphic via `as` so
 *   it can be a <section>, <aside>, <article>, etc. without extra wrappers.
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
  const classes = ["glass", className ?? ""].filter(Boolean).join(" ");
  return (
    <Tag className={classes} {...rest}>
      {children}
    </Tag>
  );
}
