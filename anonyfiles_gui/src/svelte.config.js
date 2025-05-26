import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

export default {
  preprocess: vitePreprocess(),
  // ajoute d'autres options si besoin, mais ça suffit pour la compatibilité tailwind/vite
};
