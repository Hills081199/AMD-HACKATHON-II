import type { Config } from "tailwindcss";

// Design tokens from stitch_atlas_learning_path_graph/atlas_learning_system/DESIGN.md
// ("Atlas Learning System" — Modern Glassmorphic, deep indigo/cyan/emerald palette).
const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: "#0b1326",
        "surface-dim": "#0b1326",
        "surface-bright": "#31394d",
        "surface-container-lowest": "#060e20",
        "surface-container-low": "#131b2e",
        "surface-container": "#171f33",
        "surface-container-high": "#222a3d",
        "surface-container-highest": "#2d3449",
        "surface-variant": "#2d3449",
        "on-surface": "#dae2fd",
        "on-surface-variant": "#c7c4d7",
        "inverse-surface": "#dae2fd",
        "inverse-on-surface": "#283044",
        outline: "#908fa0",
        "outline-variant": "#464554",
        "surface-tint": "#c0c1ff",
        primary: "#c0c1ff",
        "on-primary": "#1000a9",
        "primary-container": "#8083ff",
        "on-primary-container": "#0d0096",
        "inverse-primary": "#494bd6",
        secondary: "#4cd7f6",
        "on-secondary": "#003640",
        "secondary-container": "#03b5d3",
        "on-secondary-container": "#00424e",
        tertiary: "#4edea3",
        "on-tertiary": "#003824",
        "tertiary-container": "#00885d",
        "on-tertiary-container": "#000703",
        error: "#ffb4ab",
        "on-error": "#690005",
        "error-container": "#93000a",
        "on-error-container": "#ffdad6",
        "primary-fixed": "#e1e0ff",
        "primary-fixed-dim": "#c0c1ff",
        "on-primary-fixed": "#07006c",
        "on-primary-fixed-variant": "#2f2ebe",
        "secondary-fixed": "#acedff",
        "secondary-fixed-dim": "#4cd7f6",
        "on-secondary-fixed": "#001f26",
        "on-secondary-fixed-variant": "#004e5c",
        "tertiary-fixed": "#6ffbbe",
        "tertiary-fixed-dim": "#4edea3",
        "on-tertiary-fixed": "#002113",
        "on-tertiary-fixed-variant": "#005236",
        background: "#0b1326",
        "on-background": "#dae2fd",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      fontSize: {
        "display-lg": ["48px", { lineHeight: "56px", letterSpacing: "-0.02em", fontWeight: "700" }],
        "headline-lg": ["32px", { lineHeight: "40px", letterSpacing: "-0.01em", fontWeight: "600" }],
        "headline-lg-mobile": ["24px", { lineHeight: "32px", fontWeight: "600" }],
        "body-md": ["16px", { lineHeight: "24px", fontWeight: "400" }],
        "stats-mono": ["14px", { lineHeight: "20px", letterSpacing: "0.05em", fontWeight: "500" }],
        "label-caps": ["12px", { lineHeight: "16px", fontWeight: "700" }],
      },
      // Per DESIGN.md's own "rounded" token scale, not the inline Tailwind
      // config baked into the per-screen code.html exports — those omit a
      // real `full: 9999px`, which would turn avatars/pills into rounded
      // squares instead of circles.
      borderRadius: {
        sm: "0.125rem",
        DEFAULT: "0.25rem",
        md: "0.375rem",
        lg: "0.5rem",
        xl: "0.75rem",
        full: "9999px",
      },
      spacing: {
        "base-unit": "4px",
        "container-max": "1280px",
        "margin-desktop": "40px",
        "margin-mobile": "16px",
        gutter: "24px",
      },
    },
  },
  plugins: [],
};

export default config;
