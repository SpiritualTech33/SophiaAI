"use client";

import { useEffect, useRef } from "react";

/**
 * Mental Model:
 *   Draws a drifting starfield on a fixed full-viewport canvas behind every
 *   page. Star count scales with the viewport so small screens stay cheap.
 *   Most stars are blue-white; a small minority glow warm gold, echoing the
 *   divine-light accent of the corpus. Under reduced-motion we paint a single
 *   static frame and stop — no animation loop. The loop also pauses when the
 *   tab is hidden. Faithful port of cosmos.js initStarfield().
 */

type Star = {
  x: number;
  y: number;
  r: number;
  a: number;
  tw: number;
  vy: number;
  color: string;
};

const prefersReducedMotion = () =>
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

export default function Starfield() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let stars: Star[] = [];
    let rafId = 0;

    function size() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas!.width = window.innerWidth * dpr;
      canvas!.height = window.innerHeight * dpr;
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
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

    function paint(animate: boolean) {
      ctx!.clearRect(0, 0, window.innerWidth, window.innerHeight);
      for (const s of stars) {
        if (animate) {
          s.a += s.tw;
          if (s.a > 0.9 || s.a < 0.2) s.tw *= -1;
          s.y += s.vy;
          if (s.y > window.innerHeight) {
            s.y = 0;
            s.x = Math.random() * window.innerWidth;
          }
        }
        ctx!.globalAlpha = s.a;
        ctx!.fillStyle = s.color;
        ctx!.beginPath();
        ctx!.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx!.fill();
      }
      ctx!.globalAlpha = 1;
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

    function onVisibility() {
      if (document.hidden) {
        cancelAnimationFrame(rafId);
      } else if (!prefersReducedMotion()) {
        loop();
      }
    }

    window.addEventListener("resize", start);
    document.addEventListener("visibilitychange", onVisibility);
    start();

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener("resize", start);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, []);

  return <canvas id="starfield" ref={canvasRef} aria-hidden="true" />;
}
