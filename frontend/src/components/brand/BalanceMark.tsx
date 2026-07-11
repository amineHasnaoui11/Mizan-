import { motion } from "framer-motion";

/**
 * Marque « ميزان » — une balance stylisée. Le fléau s'incline légèrement
 * (micro-interaction signature) puis se stabilise : l'équilibre, la justice.
 */
export function BalanceMark({ size = 28, animate = true }: { size?: number; animate?: boolean }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <motion.g
        initial={animate ? { rotate: -7 } : false}
        animate={animate ? { rotate: 0 } : undefined}
        transition={{ type: "spring", stiffness: 120, damping: 8, delay: 0.1 }}
        style={{ transformOrigin: "16px 7px" }}
      >
        {/* fléau */}
        <line x1="6" y1="9" x2="26" y2="9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        {/* plateaux */}
        <path d="M6 9 L2.5 15 h7 Z" fill="currentColor" opacity="0.9" />
        <path d="M26 9 L22.5 15 h7 Z" fill="currentColor" opacity="0.9" />
      </motion.g>
      {/* mât + socle */}
      <line x1="16" y1="4" x2="16" y2="26" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <circle cx="16" cy="4" r="2" fill="currentColor" />
      <path d="M11 27 h10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
