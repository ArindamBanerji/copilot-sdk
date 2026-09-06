import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const HOST = process.env.COPILOT_HOST || "127.0.0.1";

export default defineConfig({
  plugins: [react()],
  define: {
    "import.meta.env.VITE_COPILOT_HOST": JSON.stringify(HOST),
    "import.meta.env.VITE_API_URL": JSON.stringify(`http://${HOST}:8010`),
  },
  server: {
    host: "127.0.0.1",
    proxy: {
      "/api": `http://${HOST}:8010`,
    },
  },
});
