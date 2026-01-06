module.exports = {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "Inter var", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
      },
      colors: {
        bg: "var(--bg)",
        card: "var(--card)",
        muted: "var(--muted)",
        border: "var(--border)",
        text: "var(--text)",
        primary: "var(--primary)",
      },
      boxShadow: {
        soft: "0 10px 30px -12px rgba(0,0,0,0.15)",
      },
    },
  },
  plugins: [require("@tailwindcss/forms"), require("@tailwindcss/typography")],
};
