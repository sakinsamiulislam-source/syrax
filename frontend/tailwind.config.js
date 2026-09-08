/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#090D16",
        foreground: "#F1F5F9",
        card: {
          DEFAULT: "#0F172A",
          foreground: "#F8FAFC",
        },
        border: "#1E293B",
        accent: {
          brand: "#6366F1",
          cyan: "#06B6D4",
          emerald: "#10B981",
          amber: "#F59E0B",
          rose: "#F43F5E",
        },
        slate: {
          850: "#131C31",
          900: "#0B1120",
          950: "#060913",
        }
      },
      boxShadow: {
        glow: "0 0 25px -5px rgba(99, 102, 241, 0.15)",
        "glow-emerald": "0 0 25px -5px rgba(16, 185, 129, 0.15)",
        "glow-rose": "0 0 25px -5px rgba(244, 63, 94, 0.15)",
      }
    },
  },
  plugins: [],
};
