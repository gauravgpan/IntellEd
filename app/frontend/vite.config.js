import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Lets the dev server call /api/... without a CORS round-trip;
      // the Django backend is assumed at localhost:8000 (see backend/.env.example).
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
