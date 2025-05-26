// vite.config.ts
import { defineConfig } from "file:///C:/Users/simongrossi/Documents/GitHub/anonyfiles/anonyfiles-gui/node_modules/vite/dist/node/index.js";
import { svelte } from "file:///C:/Users/simongrossi/Documents/GitHub/anonyfiles/anonyfiles-gui/node_modules/@sveltejs/vite-plugin-svelte/src/index.js";
import path from "path";
var __vite_injected_original_dirname = "C:\\Users\\simongrossi\\Documents\\GitHub\\anonyfiles\\anonyfiles-gui";
var host = process.env.TAURI_DEV_HOST;
var vite_config_default = defineConfig(async () => ({
  root: "./",
  plugins: [svelte()],
  clearScreen: false,
  server: {
    port: 5173,
    strictPort: true,
    host: host || false,
    hmr: host ? {
      protocol: "ws",
      host,
      port: 1421
    } : void 0,
    watch: {
      ignored: ["**/src-tauri/**"]
    },
    fs: {
      strict: false
    }
  },
  resolve: {
    alias: {
      "@tauri-apps/api": path.resolve(__vite_injected_original_dirname, "node_modules/@tauri-apps/api")
    }
  }
}));
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFxzaW1vbmdyb3NzaVxcXFxEb2N1bWVudHNcXFxcR2l0SHViXFxcXGFub255ZmlsZXNcXFxcYW5vbnlmaWxlcy1ndWlcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfZmlsZW5hbWUgPSBcIkM6XFxcXFVzZXJzXFxcXHNpbW9uZ3Jvc3NpXFxcXERvY3VtZW50c1xcXFxHaXRIdWJcXFxcYW5vbnlmaWxlc1xcXFxhbm9ueWZpbGVzLWd1aVxcXFx2aXRlLmNvbmZpZy50c1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9pbXBvcnRfbWV0YV91cmwgPSBcImZpbGU6Ly8vQzovVXNlcnMvc2ltb25ncm9zc2kvRG9jdW1lbnRzL0dpdEh1Yi9hbm9ueWZpbGVzL2Fub255ZmlsZXMtZ3VpL3ZpdGUuY29uZmlnLnRzXCI7aW1wb3J0IHsgZGVmaW5lQ29uZmlnIH0gZnJvbSBcInZpdGVcIjtcclxuaW1wb3J0IHsgc3ZlbHRlIH0gZnJvbSBcIkBzdmVsdGVqcy92aXRlLXBsdWdpbi1zdmVsdGVcIjtcclxuaW1wb3J0IHBhdGggZnJvbSBcInBhdGhcIjtcclxuXHJcbi8vIEB0cy1leHBlY3QtZXJyb3IgcHJvY2VzcyBpcyBhIG5vZGVqcyBnbG9iYWxcclxuY29uc3QgaG9zdCA9IHByb2Nlc3MuZW52LlRBVVJJX0RFVl9IT1NUO1xyXG5cclxuZXhwb3J0IGRlZmF1bHQgZGVmaW5lQ29uZmlnKGFzeW5jICgpID0+ICh7XHJcbiAgcm9vdDogJy4vJyxcclxuICBwbHVnaW5zOiBbc3ZlbHRlKCldLFxyXG4gIGNsZWFyU2NyZWVuOiBmYWxzZSxcclxuICBzZXJ2ZXI6IHtcclxuICAgIHBvcnQ6IDUxNzMsXHJcbiAgICBzdHJpY3RQb3J0OiB0cnVlLFxyXG4gICAgaG9zdDogaG9zdCB8fCBmYWxzZSxcclxuICAgIGhtcjogaG9zdFxyXG4gICAgICA/IHtcclxuICAgICAgICAgIHByb3RvY29sOiBcIndzXCIsXHJcbiAgICAgICAgICBob3N0LFxyXG4gICAgICAgICAgcG9ydDogMTQyMSxcclxuICAgICAgICB9XHJcbiAgICAgIDogdW5kZWZpbmVkLFxyXG4gICAgd2F0Y2g6IHtcclxuICAgICAgaWdub3JlZDogW1wiKiovc3JjLXRhdXJpLyoqXCJdLFxyXG4gICAgfSxcclxuICAgIGZzOiB7XHJcbiAgICAgIHN0cmljdDogZmFsc2VcclxuICAgIH1cclxuICB9LFxyXG4gIHJlc29sdmU6IHtcclxuICAgIGFsaWFzOiB7XHJcbiAgICAgICdAdGF1cmktYXBwcy9hcGknOiBwYXRoLnJlc29sdmUoX19kaXJuYW1lLCAnbm9kZV9tb2R1bGVzL0B0YXVyaS1hcHBzL2FwaScpXHJcbiAgICB9XHJcbiAgfVxyXG59KSk7XHJcbiJdLAogICJtYXBwaW5ncyI6ICI7QUFBNlgsU0FBUyxvQkFBb0I7QUFDMVosU0FBUyxjQUFjO0FBQ3ZCLE9BQU8sVUFBVTtBQUZqQixJQUFNLG1DQUFtQztBQUt6QyxJQUFNLE9BQU8sUUFBUSxJQUFJO0FBRXpCLElBQU8sc0JBQVEsYUFBYSxhQUFhO0FBQUEsRUFDdkMsTUFBTTtBQUFBLEVBQ04sU0FBUyxDQUFDLE9BQU8sQ0FBQztBQUFBLEVBQ2xCLGFBQWE7QUFBQSxFQUNiLFFBQVE7QUFBQSxJQUNOLE1BQU07QUFBQSxJQUNOLFlBQVk7QUFBQSxJQUNaLE1BQU0sUUFBUTtBQUFBLElBQ2QsS0FBSyxPQUNEO0FBQUEsTUFDRSxVQUFVO0FBQUEsTUFDVjtBQUFBLE1BQ0EsTUFBTTtBQUFBLElBQ1IsSUFDQTtBQUFBLElBQ0osT0FBTztBQUFBLE1BQ0wsU0FBUyxDQUFDLGlCQUFpQjtBQUFBLElBQzdCO0FBQUEsSUFDQSxJQUFJO0FBQUEsTUFDRixRQUFRO0FBQUEsSUFDVjtBQUFBLEVBQ0Y7QUFBQSxFQUNBLFNBQVM7QUFBQSxJQUNQLE9BQU87QUFBQSxNQUNMLG1CQUFtQixLQUFLLFFBQVEsa0NBQVcsOEJBQThCO0FBQUEsSUFDM0U7QUFBQSxFQUNGO0FBQ0YsRUFBRTsiLAogICJuYW1lcyI6IFtdCn0K
