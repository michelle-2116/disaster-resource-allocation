/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        hazard: "#ef4444",
        safe: "#22c55e",
        brand: "#2563eb"
      }
    },
  },
  plugins: [],
}