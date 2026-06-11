"use client";

import { useEffect, useRef, useState } from "react";
import { MusicIcon } from "./icons";

/**
 * Mental Model:
 *   The cosmic bed. A floating glass orb that plays a looping ambient track —
 *   the sound of being adrift in the universe. Music never autoplays (browsers
 *   block it, and silence-by-default is respectful); the listener summons it
 *   with a click. Hovering the orb reveals a volume slider, and the chosen
 *   volume is remembered across sessions. Tracks are self-hosted under
 *   /public/audio so playback is full and free for every visitor — no Spotify,
 *   no login, no licensing strings. Drop more files into TRACKS to grow the bed.
 */

type Track = { src: string; title: string };

const TRACKS: Track[] = [
  { src: "/audio/cosmic-ambient.mp3", title: "Cosmic Drift" },
];

const VOL_KEY = "cosmic-music-volume";

export default function CosmicPlayer() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const [volume, setVolume] = useState(0.4);
  const [failed, setFailed] = useState(false);

  // Restore the listener's last volume.
  useEffect(() => {
    const stored = Number(localStorage.getItem(VOL_KEY));
    if (!Number.isNaN(stored) && stored >= 0 && stored <= 1) setVolume(stored);
  }, []);

  // Keep the audio element and storage in sync with the volume slider.
  useEffect(() => {
    if (audioRef.current) audioRef.current.volume = volume;
    localStorage.setItem(VOL_KEY, String(volume));
  }, [volume]);

  async function toggle() {
    const audio = audioRef.current;
    if (!audio) return;
    if (playing) {
      audio.pause();
      return;
    }
    try {
      await audio.play();
    } catch {
      setFailed(true);
      setPlaying(false);
    }
  }

  if (TRACKS.length === 0) return null;

  const label = playing ? "Pause ambient music" : "Play ambient music";

  return (
    <div className={`cosmic-player ${playing ? "is-playing" : ""}`}>
      <audio
        ref={audioRef}
        src={TRACKS[0].src}
        loop
        preload="none"
        onPlay={() => {
          setFailed(false);
          setPlaying(true);
        }}
        onPause={() => setPlaying(false)}
        onError={() => {
          setFailed(true);
          setPlaying(false);
        }}
      />
      <input
        className="cosmic-player-vol"
        type="range"
        min={0}
        max={1}
        step={0.01}
        value={volume}
        onChange={(e) => setVolume(Number(e.target.value))}
        aria-label="Music volume"
      />
      <button
        type="button"
        className="cosmic-player-btn"
        onClick={toggle}
        aria-pressed={playing}
        aria-label={label}
        title={
          failed
            ? "No track found — add an .mp3 to web/public/audio/"
            : label
        }
      >
        {playing ? (
          <span className="eq" aria-hidden="true">
            <i />
            <i />
            <i />
            <i />
          </span>
        ) : (
          <MusicIcon />
        )}
      </button>
    </div>
  );
}
