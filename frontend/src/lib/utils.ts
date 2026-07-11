import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Fusionne des classes Tailwind sans conflits (cn = classnames). */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Couleur sémantique d'une note selon le ratio obtenu/max. */
export function couleurNote(obtenus: number, max: number): string {
  if (max <= 0) return "var(--muted, #7C8B86)";
  const r = obtenus / max;
  if (r >= 0.999) return "#2E7D32";
  if (r <= 0.001) return "#C0442E";
  return "#E8A13A";
}
