import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        serif: ['Georgia', '"Times New Roman"', 'serif'],
        sans: [
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          'Segoe UI',
          'Roboto',
          'sans-serif',
        ],
      },
      colors: {
        paper: {
          50: "#fcfbf6",
          100: "#f6f3eb",
          200: "#ece6d6",
          300: "#d9cfb6",
        },
        ink: {
          900: "#16181d",
          800: "#222630",
          700: "#3a3f4b",
          500: "#6b7180",
          300: "#a7adba",
        },
        accent: {
          50: "#fdf2ec",
          400: "#e08a55",
          500: "#cf6a30",
          600: "#a8521f",
          700: "#7d3a14",
        },
        forest: {
          500: "#3d6b4a",
          600: "#2c5237",
        },
      },
    },
  },
  plugins: [],
};

export default config;
