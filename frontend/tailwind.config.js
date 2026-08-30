/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef8ff",
          500: "#1179e6",
          700: "#0757ad"
        }
      }
    }
  },
  plugins: []
};
