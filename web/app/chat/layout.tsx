/**
 * Mental Model:
 *   The chat workspace wants the full viewport, not the centered 1200px
 *   column the public pages use. Wrapping it in `.chat-body` flips the
 *   `.site-main` width rule (see globals.css) without touching the root layout.
 */
export default function ChatLayout({ children }: { children: React.ReactNode }) {
  return <div className="chat-body">{children}</div>;
}
