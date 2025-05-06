import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte"; // <--- Ajoutez cette ligne

// @ts-expect-error process is a nodejs global
const host = process.env.TAURI_DEV_HOST;

// https://vitejs.dev/config/
export default defineConfig(async () => ({
  // Ajoutez cette ligne pour définir la racine du projet frontend
  root: './',

  plugins: [svelte()], // <--- Ajoutez cette ligne pour activer le plugin Svelte

  // Vite options tailored for Tauri development and only applied in `tauri dev` or `tauri build`
  //
  // 1. prevent vite from obscuring rust errors
  clearScreen: false,
  // 2. tauri expects a fixed port, fail if that port is not available
  server: {
    port: 5173, // Assurez-vous que c'est bien 5173
    strictPort: true,
    host: host || false,
    hmr: host
      ? {
          protocol: "ws",
          host,
          port: 1421,
        }
      : undefined,
    watch: {
      // 3. tell vite to ignore watching `src-tauri`
      ignored: ["**/src-tauri/**"],
    },
  },
}));