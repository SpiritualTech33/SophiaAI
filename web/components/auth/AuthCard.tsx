"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import GlassPanel from "@/components/cosmic/GlassPanel";

/**
 * Mental Model:
 *   The gate. One card serves both login and registration — the `mode` decides
 *   the copy and which BFF endpoint it posts to. On success the session cookie
 *   is already set server-side, so we just navigate into /chat and refresh so
 *   the server re-reads the new session. Errors surface inline, calmly.
 */
type Mode = "login" | "register";

const COPY: Record<Mode, {
  title: string;
  subtitle: string;
  submit: string;
  endpoint: string;
  altText: string;
  altHref: string;
  altLink: string;
}> = {
  login: {
    title: "Welcome back",
    subtitle: "Return to the portal.",
    submit: "Sign in",
    endpoint: "/api/auth/login",
    altText: "New here?",
    altHref: "/register",
    altLink: "Create an account",
  },
  register: {
    title: "Enter the Portal",
    subtitle: "Begin your dialogue with Sophia.",
    submit: "Create account",
    endpoint: "/api/auth/register",
    altText: "Already with us?",
    altHref: "/login",
    altLink: "Sign in",
  },
};

export default function AuthCard({ mode }: { mode: Mode }) {
  const router = useRouter();
  const copy = COPY[mode];

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (busy) return;
    setError("");
    setBusy(true);
    try {
      const res = await fetch(copy.endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const data = (await res.json().catch(() => null)) as { message?: string } | null;
        setError(data?.message ?? "Something went wrong. Please try again.");
        return;
      }
      router.push("/chat");
      router.refresh();
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <GlassPanel as="section" className="gate">
      <h1>{copy.title}</h1>
      <p className="subtitle">{copy.subtitle}</p>

      <form onSubmit={onSubmit} noValidate>
        <p className="form-error" role="alert">
          {error}
        </p>

        <div className="field">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            className="input"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div className="field">
          <label htmlFor="password">Password</label>
          <div className="password-wrap">
            <input
              id="password"
              className="input"
              type={showPassword ? "text" : "password"}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? "Hide" : "Show"}
            </button>
          </div>
        </div>

        <button type="submit" className="btn btn-primary" style={{ width: "100%" }} disabled={busy}>
          {busy ? "One moment…" : copy.submit}
        </button>
      </form>

      <p className="alt">
        {copy.altText} <Link href={copy.altHref}>{copy.altLink}</Link>
      </p>
    </GlassPanel>
  );
}
