import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// ==================================================
// CONFIGURACION DEL SERVIDOR COTESPC
// ==================================================

export default defineConfig(({ mode }) => {

  // Cargar las variables de entorno del proyecto
  const env = loadEnv(mode, process.cwd(), 'COTESPC_');

  // Dirección del servidor backend
  const backendHost = env.COTESPC_BACKEND_HOST || '127.0.0.1';

  console.log(`[Vite] Servidor backend: ${backendHost}`);

  return {
    plugins: [react()],

    server: {
      host: '127.0.0.1',
      port: 5173,
      strictPort: true,

      proxy: {

        // ============================================
        // CONSULTAR PERSONA - PUERTO 8000
        // ============================================
        '/api/personas': {
          target: `http://${backendHost}:8000`,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
        // ============================================
        // AUTENTICACION - PUERTO 8001
        // ============================================
        '/api/auth': {
          target: `http://${backendHost}:8001`,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },

        // ============================================
        // CREAR PERSONA - PUERTO 8002
        // ============================================
        '/api/crear-persona': {
          target: `http://${backendHost}:8002`,
          changeOrigin: true,
          rewrite: (path) =>
            path.replace(/^\/api\/crear-persona/, ''),
        },
        
        // ============================================
        // MODIFICAR PERSONA - PUERTO 8003
        // ============================================
        '/api/modificar-persona': {
          target: `http://${backendHost}:8003`,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
        // ============================================
        // AUDITORÍA - PUERTO 8004
        // ============================================
        '/api/auditoria': {
          target: `http://${backendHost}:8004`,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
  };
});