import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  plugins: [],
  root: resolve(__dirname, '..'),
  base: '/public/static/',
  server: {
    host: '0.0.0.0',
    port: 3000,
    open: false,
    watch: {
      usePolling: true,
      disableGlobbing: false,
    },
  },
  resolve: {
    extensions: ['.js', '.json'],
    alias: {
      '~bootstrap': resolve(__dirname, '../../node_modules/bootstrap'),
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
        main: resolve(__dirname, '../js/main.js'),
      },
      output: {
        chunkFileNames: undefined,
      },
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        api: 'modern-compiler',
        // Suppress Sass deprecation warnings that are caused by Bootstrap.
        // See this issue for more details: https://github.com/twbs/bootstrap/issues/40962
        silenceDeprecations: ['color-functions', 'import', 'global-builtin'],
      },
    },
  },
});
