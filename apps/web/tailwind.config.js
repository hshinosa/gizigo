/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["Plus Jakarta Sans", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        brand: {
          50: "#eef9f3",
          100: "#d6f1e2",
          200: "#aee2c4",
          300: "#7ecf9f",
          400: "#4eb778",
          500: "#2f9b5c",
          600: "#237b48",
          700: "#1d623b",
          800: "#1a4f31",
          900: "#16412a",
        },
      },
      borderRadius: {
        xl: "1rem",
        "2xl": "1.25rem",
      },
    },
  },
  plugins: [require("@tailwindcss/forms")],
};
