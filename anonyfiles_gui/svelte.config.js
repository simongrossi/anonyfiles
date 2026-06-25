import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

export default {
  // vitePreprocess (fourni par vite-plugin-svelte) gère TS/PostCSS et remplace
  // svelte-preprocess, recommandé avec Svelte 5.
  preprocess: vitePreprocess(),
};
