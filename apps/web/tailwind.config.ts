import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        locked: "#B4B2A9",
        unlocked: "#378ADD",
        completed: "#639922",
      },
    },
  },
  plugins: [],
};

export default config;
