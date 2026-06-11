/**
 * Mental Model:
 *   The cytoplasm. A single fixed, blurred aurora layer that drifts slowly
 *   behind the glass — soft pools of azure, violet, cyan and gold light. It
 *   gives the interface the feeling of a living cell: depth that breathes
 *   rather than a flat black void. Pure presentation, no logic; all motion
 *   lives in `.aurora` in globals.css and is gated behind prefers-reduced-motion.
 */
export default function Aurora() {
  return <div className="aurora" aria-hidden="true" />;
}
