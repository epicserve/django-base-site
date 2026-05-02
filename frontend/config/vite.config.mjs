import { defineConfig } from 'vite';
import { resolve } from 'path';
import vue from '@vitejs/plugin-vue';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  root: resolve(__dirname, '..'),
  base: '/public/static/dist/js/',
  server: {
    host: '0.0.0.0',
    port: 3000,
    origin: 'http://localhost:3000',
    open: false,
    watch: {
      usePolling: true,
      disableGlobbing: false,
    },
  },
  resolve: {
    extensions: ['.js', '.vue', '.json'],
    alias: {
      '@': resolve(__dirname, '../js'),
    },
  },
  build: {
    outDir: resolve(__dirname, '../../public/static/dist/js'),
    assetsDir: '',
    manifest: true,
    emptyOutDir: true,
    target: 'es2015',
    rollupOptions: {
      input: {
        app: resolve(__dirname, '../js/app.js'),
      },
      output: {
        chunkFileNames: undefined,
      },
    },
  },
});
