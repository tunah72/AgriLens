import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        background: "var(--color-background)",
        foreground: "var(--color-foreground)",
        surface: {
          DEFAULT: "var(--color-surface)",
          sidebar: "var(--color-surface-sidebar)",
          raised: "var(--color-surface-raised)",
          border: "var(--color-surface-border)",
        },
        interactive: {
          hover: "var(--color-interactive-hover)",
          active: "var(--color-interactive-active)",
        },
        "text-secondary": "var(--color-text-secondary)",
        "text-tertiary": "var(--color-text-tertiary)",
        "surface-hover": "var(--color-surface-hover)",
        "border-hover": "var(--color-border-hover)",
        "input-bg": "var(--color-input-bg)",
        "input-disabled": "var(--color-input-disabled)",
        "claude-orange": "var(--color-claude-orange)",
        "claude-orange-hover": "var(--color-claude-orange-hover)",
        "claude-orange-text": "var(--color-claude-orange-text)",
        "claude-text": "var(--color-claude-text)",
        "claude-muted": "var(--color-claude-muted)",
        healthy: {
          50: "#f0fdf4",
          500: "#16a34a",
          700: "#15803d",
        },
        warning: {
          50: "#fffbeb",
          500: "#d97706",
          700: "#b45309",
        },
        danger: {
          50: "#fef2f2",
          500: "#dc2626",
          700: "#b91c1c",
        },
        info: {
          50: "#eff6ff",
          500: "#2563eb",
          700: "#1d4ed8",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        display: ["var(--font-bevietnam)", "var(--font-inter)", "sans-serif"],
        serif: ["var(--font-playfair)", "Georgia", "serif"],
      },
      spacing: {
        '18': '4.5rem',
        '112': '28rem',
        '128': '32rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      }
    },
  },
  plugins: [],
};

export default config;
