import type { ReactNode } from "react";
import Wordmark from "@/components/cosmic/Wordmark";

/**
 * Mental Model:
 *   The top bar for the public pages (landing, login, register): the SOPHIA
 *   wordmark on the left, optional navigation on the right. Sits above the
 *   starfield (z-index handled by .site-header).
 */
export default function SiteHeader({ nav }: { nav?: ReactNode }) {
  return (
    <header className="site-header">
      <Wordmark />
      {nav ? <nav className="header-toggles">{nav}</nav> : null}
    </header>
  );
}
