/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        dossier: {
          50: "#f2f5f9",
          100: "#e2e8f2",
          200: "#ccd7e5",
          300: "#afbed1",
          400: "#6c819e",
          500: "#526781",
          700: "#2c3b50",
          900: "#151d27",
        },
        accent: {
          blue: "#516b87",
          slate: "#4d5d6f",
          red: "#8e4a49",
        },
      },
      boxShadow: {
        dossier: "0 10px 30px -22px rgba(20, 30, 40, 0.7)",
      },
    },
  },
  plugins: [],
};
