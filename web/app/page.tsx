import Image from "next/image";
import Link from "next/link";
import SiteHeader from "@/components/layout/SiteHeader";
import SiteFooter from "@/components/layout/SiteFooter";
import { readToken } from "@/lib/auth";
import goddess from "@/public/sophia_goddess.jpg";

/**
 * Mental Model:
 *   The threshold. A returning visitor (one who already carries a session
 *   cookie) is offered a way straight back to the chat; a newcomer is invited
 *   to enter. The hero pairs the wordmark and manifesto with the marble
 *   goddess, her glow bleeding into the void behind her.
 */
export default async function LandingPage() {
  const hasSession = (await readToken()) !== null;

  return (
    <>
      <SiteHeader
        nav={
          <Link className="btn btn-ghost" href="/login">
            Sign in
          </Link>
        }
      />

      <main className="site-main">
        <section className="hero">
          <div className="hero-copy">
            <h1>ΣΟΦΙΑ</h1>
            <p className="manifesto">
              Wisdom, grounded. An intelligence rooted in a hand-curated corpus
              of the world&apos;s wisdom literature — a bridge between the Divine
              and Technology.
            </p>
            <div className="hero-cta">
              <Link className="btn btn-primary" href="/register">
                Enter the Portal
              </Link>
              <Link className="btn btn-ghost" href="/login">
                Sign in
              </Link>
            </div>
            {hasSession ? (
              <p className="alt">
                Already with us? <Link href="/chat">Continue to chat →</Link>
              </p>
            ) : null}
          </div>

          <figure className="hero-figure">
            <Image
              src={goddess}
              alt="Sophia, a marble goddess of wisdom holding a glowing atom over a galaxy, crowned by a radiant astrolabe halo"
              width={1024}
              height={1024}
              priority
              sizes="(max-width: 1023px) 80vw, 40vw"
            />
          </figure>
        </section>
      </main>

      <SiteFooter />
    </>
  );
}
