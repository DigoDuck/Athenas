import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    // Bind mounts on Windows do not emit file events.
    watch: { usePolling: true },
    proxy: { "/api": process.env.API_PROXY_TARGET ?? "http://backend:8000" },
  },
});
