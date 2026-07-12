// Design system Mizan (aligné sur le web) — vert-encre + terracotta.
export const colors = {
  ink: "#0E4D45",
  inkSoft: "#16665B",
  accent: "#E07A3F",
  accentDeep: "#C15F28",
  paper: "#FAF7F2",
  surface: "#FFFFFF",
  line: "#E9E2D8",
  muted: "#7C8B86",
  mutedStrong: "#4A5A55",
  scoreFull: "#2E7D32",
  scorePartial: "#E8A13A",
  scoreZero: "#C0442E",
  white: "#FFFFFF",
};

export function couleurNote(obtenus: number, max: number): string {
  if (max <= 0) return colors.muted;
  const r = obtenus / max;
  if (r >= 0.999) return colors.scoreFull;
  if (r <= 0.001) return colors.scoreZero;
  return colors.scorePartial;
}

export const radius = { md: 12, lg: 16, xl: 20 };
