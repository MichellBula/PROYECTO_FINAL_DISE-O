
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// ==================================================
// CONFIGURACIÓN DEL FRONTEND
// API GATEWAY - COTESPC
// ==================================================

export default defineConfig({
  plugins: [react()],

  server: {
    // Servidor de desarrollo React
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,

    // ==================================================
    // TODAS LAS SOLICITUDES PASAN POR LA API GATEWAY
    // ==================================================

    proxy: {
      "/api": {
        // Túnel SSH hacia la Gateway Docker de CotesPC
        target:
  process.env.FRONTEND_API_TARGET ||
  "http://127.0.0.1:8007",

        changeOrigin: true,

        // No eliminamos /api.
        // La Gateway ya define sus rutas con ese prefijo.
      },
    },
  },
});
