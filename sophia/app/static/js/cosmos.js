/* =========================================================================
   cosmos.js — shared helpers for SophiaAI's front end.

   Single responsibility per export:
     - token storage (localStorage)
     - authFetch: fetch with Bearer token + 401 handling
     - requireAuth: client-side guard for protected pages
     - initStarfield: the living background (reduced-motion aware)

   No framework. ES module. Imported by auth.js and chat.js.
   ========================================================================= */

const TOKEN_KEY = "sophia_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

/**
 * Mental Model:
 *   Every protected API call goes through here. It attaches the JWT and,
 *   if the server rejects it (401), clears the dead token and sends the
 *   user back to /login. Callers only handle the happy path + real errors.
 */
export async function authFetch(url, options = {}) {
  const token = getToken();
  const headers = new Headers(options.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, { ...options, headers });
  if (response.status === 401) {
    clearToken();
    window.location.replace("/login");
    throw new Error("Session expired");
  }
  return response;
}

/** Redirect to /login if no token is present. Called by protected pages. */
export function requireAuth() {
  if (!getToken()) {
    window.location.replace("/login");
    return false;
  }
  return true;
}

const prefersReducedMotion = () =>
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/**
 * Mental Model:
 *   Draws a drifting starfield on #starfield. Star count scales with the
 *   viewport so small screens stay cheap. Most stars are blue-white; a small
 *   minority glow warm gold, echoing the divine-light accent of the corpus.
 *   Under reduced-motion we paint a single static frame and stop — no
 *   animation loop at all. The loop also pauses when the tab is hidden.
 */
export function initStarfield() {
  const canvas = document.getElementById("starfield");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  let stars = [];
  let rafId = null;

  function size() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = window.innerWidth * dpr;
    canvas.height = window.innerHeight * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function seed() {
    const area = window.innerWidth * window.innerHeight;
    const count = Math.min(220, Math.floor(area / 9000));
    stars = Array.from({ length: count }, () => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      r: Math.random() * 1.4 + 0.3,
      a: Math.random() * 0.6 + 0.2,
      tw: Math.random() * 0.02 + 0.004,
      vy: Math.random() * 0.06 + 0.02,
      // ~1 in 6 stars glow warm gold; the rest are cool blue-white.
      color: Math.random() < 0.16 ? "#ffe2a6" : "#cfe6ff",
    }));
  }

  function paint(animate) {
    ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
    for (const s of stars) {
      if (animate) {
        s.a += s.tw;
        if (s.a > 0.9 || s.a < 0.2) s.tw *= -1;
        s.y += s.vy;
        if (s.y > window.innerHeight) { s.y = 0; s.x = Math.random() * window.innerWidth; }
      }
      ctx.globalAlpha = s.a;
      ctx.fillStyle = s.color;
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
  }

  function loop() {
    paint(true);
    rafId = requestAnimationFrame(loop);
  }

  function start() {
    size();
    seed();
    if (prefersReducedMotion()) {
      paint(false);
      return;
    }
    cancelAnimationFrame(rafId);
    loop();
  }

  window.addEventListener("resize", start);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      cancelAnimationFrame(rafId);
    } else if (!prefersReducedMotion()) {
      loop();
    }
  });

  start();
}

document.addEventListener("DOMContentLoaded", initStarfield);