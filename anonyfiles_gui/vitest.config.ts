import { defineConfig } from 'vitest/config';
import path from 'path';

// Config Vitest isolée de vite.config.ts (build) : on n'a pas besoin du plugin
// Svelte ici car les utilitaires testés (.ts) n'importent aucun composant .svelte.
export default defineConfig({
  resolve: {
    alias: {
      $lib: path.resolve(__dirname, './src/lib'),
    },
  },
  test: {
    environment: 'node',
    include: ['src/**/*.{test,spec}.ts'],
  },
});
