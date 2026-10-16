import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // Ignorar cualquier API pública heredada de un .env del frontend.
  define: { 'import.meta.env.VITE_API_BASE_URL': JSON.stringify('/api/v1') },
  server: {
    host: '127.0.0.1', port: 5174,
    proxy: {
      '/api/v1/laboratorio': { target: 'http://127.0.0.1:8001', changeOrigin: true },
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  build: { outDir: 'dist-laboratorio', rollupOptions: { input: 'laboratorio.html' } },
});
