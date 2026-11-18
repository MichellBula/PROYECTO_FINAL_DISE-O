import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// ==================================================
// CONFIGURACION DEL SERVIDOR COTESPC
// ==================================================

export default defineConfig({
  plugins: [react()],

  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,

    proxy: {
      // AUTENTICACION
      '/api/auth': {
        target: 'http://100.109.132.122:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },

      // CONSULTA DE PERSONAS
      '/api/personas': {
        target: 'http://100.109.132.122:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
});