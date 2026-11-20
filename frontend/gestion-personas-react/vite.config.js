import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// ==================================================
// CONFIGURACION DEL SERVIDOR COTESPC
// ==================================================

const backendHost = process.env.COTESPC_BACKEND_HOST || '127.0.0.1';

export default defineConfig({
  plugins: [react()],

  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,

    proxy: {
      // ============================================
      // MICROSERVICIO DE AUTENTICACION - PUERTO 8001
      // ============================================
      '/api/auth': {
        target: `http://${backendHost}:8001`,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },

      // ============================================
      // MICROSERVICIO DE CONSULTA - PUERTO 8000
      // ============================================
      '/api/personas': {
        target: `http://${backendHost}:8000`,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },

      // ============================================
      // MICROSERVICIO DE CREACION - PUERTO 8002
      // ============================================
      '/api/crear-persona': {
        target: `http://${backendHost}:8002`,
        changeOrigin: true,
        rewrite: (path) =>
          path.replace(/^\/api\/crear-persona/, ''),
      },

      // ============================================
      // MICROSERVICIO DE MODIFICACION - PUERTO 8003 (TU NUEVO SERVICIO)
      // ============================================
      '/api/modificar-persona': {
        target: `http://${backendHost}:8003`,
        changeOrigin: true,
        rewrite: (path) =>
          path.replace(/^\/api\/modificar-persona/, ''),
      },
    },
  },
});