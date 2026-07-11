import type { Config } from "tailwindcss";

/**
 * Design system Mizan — « la balance ».
 * Direction : vert-encre (ardoise) + terracotta, ton cahier d'école soigné.
 * Les couleurs de NOTE (vert/ambre/rouge) sont séparées de la marque.
 */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Marque
        ink: {
          DEFAULT: "#0E4D45", // vert-encre profond (primaire)
          soft: "#16665B",
          deep: "#093831",
        },
        accent: {
          DEFAULT: "#E07A3F", // terracotta tunisien (CTA, focus)
          soft: "#EC9A6A",
          deep: "#C15F28",
        },
        paper: "#FAF7F2", // fond chaud
        surface: "#FFFFFF",
        line: "#E9E2D8", // bordures douces
        muted: {
          DEFAULT: "#7C8B86", // texte secondaire (sauge)
          strong: "#4A5A55",
        },
        // Sémantique des notes (distincte de la marque)
        score: {
          full: "#2E7D32",
          partial: "#E8A13A",
          zero: "#C0442E",
        },
      },
      fontFamily: {
        display: ['"Fraunces"', "Georgia", "serif"],
        sans: ['"IBM Plex Sans Arabic"', "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
      },
      borderRadius: {
        xl: "14px",
        "2xl": "20px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(14,77,69,0.04), 0 8px 24px -12px rgba(14,77,69,0.18)",
        lift: "0 4px 12px rgba(14,77,69,0.08), 0 18px 40px -16px rgba(14,77,69,0.28)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.4s cubic-bezier(0.22,1,0.36,1) both",
      },
    },
  },
  plugins: [],
} satisfies Config;
