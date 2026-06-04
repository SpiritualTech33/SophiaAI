/**
 * Mental Model:
 *   Sophia's face. A pure-CSS cosmic orb — a blue-white plasma sphere with an
 *   arcing energy ring and a soft glow halo. It has no logic of its own; its
 *   whole life is in CSS (.orb in globals.css). The `state` prop drives the
 *   animation: idle breathes, thinking spins fast + pulses, speaking pulses
 *   twice. Size is controlled by the caller via the `--orb-size` custom
 *   property (use the `large` flag for the 160px hero orb).
 */

export type OrbState = "idle" | "thinking" | "speaking";

type OrbProps = {
  state?: OrbState;
  large?: boolean;
  className?: string;
};

export default function Orb({ state = "idle", large = false, className }: OrbProps) {
  const classes = ["orb", large ? "orb-lg" : "", className ?? ""]
    .filter(Boolean)
    .join(" ");
  return <span className={classes} data-state={state} aria-hidden="true" />;
}
