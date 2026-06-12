import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "Segoe UI", "Helvetica Neue", "Arial", "sans-serif"],
        display: ["Avenir Next", "Inter", "Segoe UI", "sans-serif"]
      },
      colors: {
        ink: "#050816",
        panel: "#0a1024",
        electric: "#3b82f6",
        cyan: "#38bdf8"
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(59,130,246,0.2), 0 30px 80px rgba(11,35,89,0.45)"
      },
      backgroundImage: {
        grid: "linear-gradient(rgba(148,163,184,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.08) 1px, transparent 1px)"
      }
    }
  },
  plugins: []
};

export default config;
