/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brandRed: "#E8220A",
        brandYellow: "#FFB800",
        brandCream: "#FFF8F0",
      },
      fontFamily: {
        heading: ["Syne", "sans-serif"],
        body: ["DM Sans", "sans-serif"],
      },
      boxShadow: {
        card: "0 8px 24px rgba(24, 24, 24, 0.08)",
      },
    },
  },
  plugins: [],
};
