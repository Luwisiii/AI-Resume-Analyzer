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
        sheet: "3px",
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
        feed: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(400%)" },
        },
      },
      animation: {
        rise: "rise .3s cubic-bezier(.2,.7,.3,1) both",
        fade: "fade .24s ease-out both",
        feed: "feed 1.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
