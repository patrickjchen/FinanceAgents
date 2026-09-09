import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";

const config: Config = {
  darkMode: 'class',
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx}",
    "./src/components/**/*.{js,ts,jsx,tsx}",
    "./src/app/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-geist-sans)', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['var(--font-geist-mono)', 'ui-monospace', 'monospace'],
      },
      colors: {
        banker: {
          light: '#e6f0ff',
          dark: '#0a192f',
          primary: '#2563eb',
        },
        primary: {
          light: '#2563eb',
          dark: '#1e293b',
        },
        background: {
          light: '#ffffff',
          dark: '#0f172a',
        },
        foreground: "var(--foreground)",
      },
    },
  },
  plugins: [typography],
}

export default config;
