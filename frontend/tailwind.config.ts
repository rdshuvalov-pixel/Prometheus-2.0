import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        candy: {
          50: "#fff7fa",
          100: "#fdebf3",
          200: "#fbd5e5",
          300: "#f6b7d1",
          400: "#ec8fb6",
          500: "#d96a99",
          600: "#a3486f",
          700: "#7a3556",
        },
      },
    },
  },
  plugins: [],
};
export default config;
