import Link from "next/link";

/**
 * Mental Model:
 *   The SOPHIA wordmark — Cinzel, wide tracking, a white→cyan→gold gradient
 *   with a dual blue+gold glow (see `.brand` in globals.css). It doubles as
 *   the home link. Pass `href` to point it elsewhere (default: /).
 */
export default function Wordmark({ href = "/" }: { href?: string }) {
  return (
    <Link href={href} className="brand">
      SOPHIA
    </Link>
  );
}
