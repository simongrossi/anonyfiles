import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import path from "path"; // Assurez-vous que 'path' est importé

const host = process.env.TAURI_DEV_HOST;

export default defineConfig(({ command }) => ({
  root: './',
  base: command === 'build' ? './' : '/',
  plugins: [svelte()],
  clearScreen: false,
  server: {
    port: 5173,
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
      ignored: ["**/src-tauri/**"],
    },
    fs: {
      strict: false
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      input: './index.html',
    },
  },
  resolve: {
    alias: {
      // Votre alias existant pour @tauri-apps/api
      '@tauri-apps/api': path.resolve(__dirname, 'node_modules/@tauri-apps/api'),
      // AJOUT DE L'ALIAS POUR $lib :
      '$lib': path.resolve(__dirname, './src/lib') // Fait pointer $lib vers anonyfiles_gui/src/lib
    }
  }
}));