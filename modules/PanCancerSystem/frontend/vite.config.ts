import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: true,
    // Proxy API requests to the PanCancerSystem backend during development
    proxy: {
      '/api': {
        target: 'http://localhost:8007',
        changeOrigin: true,
        // Strip /api prefix since the backend doesn't use it
        rewrite: (path) => path.replace(/^\/api/, ''),
        // SSE support for streaming report generation
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq) => {
            proxyReq.setHeader('Connection', 'keep-alive');
          });
        },
      },
      '/health': {
        target: 'http://localhost:8007',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          state: ['zustand'],
          http: ['axios'],
        },
      },
    },
  },
});
