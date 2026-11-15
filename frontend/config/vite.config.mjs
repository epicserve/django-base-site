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
    // The port the browser reaches this server on. compose.yml publishes container port 3000 on HOST_PORT_VITE, which
    // differs per git worktree (scripts/worktree).
    origin: `http://localhost:${process.env.HOST_PORT_VITE || 3000}`,
    open: false,
    watch: {
      usePolling: true,
      disableGlobbing: false,
    },
  },
  resolve: {
    extensions: ['.ts', '.js', '.vue', '.json'],
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
        app: resolve(__dirname, '../js/app.ts'),
      },
      output: {
        chunkFileNames: undefined,
      },
    },
  },
});
