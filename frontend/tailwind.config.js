/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      // Line-printer stock: pale green bars, black ink, one blue stamp.
      colors: {
        paper: "#f2f4ee",
        sheet: "#ffffff",
        bar: "#e5eee1",
        ink: "#161a16",
        muted: "#5b655c",
        rule: "#ccd6c8",
        stamp: "#1c3faa",
        good: "#1e6b3d",
        mid: "#8a6412",
        low: "#a4352a",
      },
      fontFamily: {
        sans: ["Archivo", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "SFMono-Regular", "monospace"],
      },
      borderRadius: {
        sheet: "14px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(22,26,22,.04), 0 8px 24px -8px rgba(22,26,22,.12)",
      },
      keyframes: {
        rise: {
          from: { opacity: "0", transform: "translateY(10px)" },
          to: { opacity: "1", transform: "none" },
        },
        fade: {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        shine: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" },
        },
      },
      animation: {
        rise: "rise .3s cubic-bezier(.2,.7,.3,1) both",
        fade: "fade .24s ease-out both",
        shine: "shine 1.6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
