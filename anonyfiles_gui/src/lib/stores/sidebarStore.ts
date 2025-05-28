// #anonyfiles/anonyfiles_gui/src/lib/stores/sidebarStore.ts
import { writable } from 'svelte/store';

export const sidebarState = writable({
  isMobile: false,
  showSidebar: true,
});
