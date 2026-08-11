/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: { ink: "#17211f", accent: { 50: "#eef9f6", 100: "#d7f1e9", 500: "#16846b", 600: "#0f6d59", 700: "#0d5749" } },
      boxShadow: { card: "0 1px 2px rgba(17,24,39,.03), 0 8px 24px rgba(17,24,39,.035)" },
      fontFamily: { sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"] },
    },
  },
  plugins: [],
};

