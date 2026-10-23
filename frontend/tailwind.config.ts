import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
    "./stores/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0a0a0f",
        foreground: "#f3f4f6",
        card: {
          DEFAULT: "#12121a",
          foreground: "#f3f4f6",
          hover: "#181824",
          border: "#1f1f2e",
        },
        brand: {
          50: "#eef2ff",
          100: "#e0e7ff",
          200: "#c7d2fe",
          300: "#a5b4fc",
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
          800: "#3730a3",
          900: "#312e81",
          950: "#1e1b4b",
        },
        agent: {
          planner: {
            DEFAULT: "#3b82f6",
            light: "#93c5fd",
            dark: "#1d4ed8",
            bg: "rgba(59, 130, 246, 0.12)",
            border: "rgba(59, 130, 246, 0.3)",
          },
          architect: {
            DEFAULT: "#a855f7",
            light: "#d8b4fe",
            dark: "#7e22ce",
            bg: "rgba(168, 85, 247, 0.12)",
            border: "rgba(168, 85, 247, 0.3)",
          },
          coder: {
            DEFAULT: "#10b981",
            light: "#6ee7b7",
            dark: "#047857",
            bg: "rgba(16, 185, 129, 0.12)",
            border: "rgba(16, 185, 129, 0.3)",
          },
          tester: {
            DEFAULT: "#eab308",
            light: "#fde047",
            dark: "#a16207",
            bg: "rgba(234, 179, 8, 0.12)",
            border: "rgba(234, 179, 8, 0.3)",
          },
          reviewer: {
            DEFAULT: "#f97316",
            light: "#fdba74",
            dark: "#c2410c",
            bg: "rgba(249, 115, 22, 0.12)",
            border: "rgba(249, 115, 22, 0.3)",
          },
          devops: {
            DEFAULT: "#ef4444",
            light: "#fca5a5",
            dark: "#b91c1c",
            bg: "rgba(239, 68, 68, 0.12)",
            border: "rgba(239, 68, 68, 0.3)",
          },
        },
      },
      keyframes: {
        "pulse-glow": {
          "0%, 100%": {
            opacity: "1",
            boxShadow: "0 0 15px rgba(99, 102, 241, 0.4), inset 0 0 15px rgba(99, 102, 241, 0.2)",
          },
          "50%": {
            opacity: "0.7",
            boxShadow: "0 0 5px rgba(99, 102, 241, 0.1), inset 0 0 5px rgba(99, 102, 241, 0.05)",
          },
        },
        "slide-in": {
          "0%": { transform: "translateY(12px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "border-glow": {
          "0%, 100%": { borderColor: "rgba(99, 102, 241, 0.6)" },
          "50%": { borderColor: "rgba(99, 102, 241, 0.2)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
      },
      animation: {
        "pulse-glow": "pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "slide-in": "slide-in 0.3s ease-out forwards",
        "fade-in": "fade-in 0.25s ease-out forwards",
        "border-glow": "border-glow 2s ease-in-out infinite",
        shimmer: "shimmer 2s infinite",
      },
      backgroundImage: {
        "cyber-grid": "radial-gradient(circle, rgba(99, 102, 241, 0.08) 1px, transparent 1px)",
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
      },
    },
  },
  plugins: [],
};

export default config;
