<!-- #anonyfiles/anonyfiles_gui/src/lib/components/Header.svelte -->
<script lang="ts">
  export let title: string = 'Anonyfiles';
  import { sidebarState } from '../stores/sidebarStore';
</script>

<header class="w-full h-16 px-4 flex items-center justify-between fixed top-0 z-50 bg-zinc-900 text-white border-b border-zinc-800">
  <!-- Logo (clair/sombre auto) -->
  <div class="flex items-center gap-2">
    <img src="/anonyfiles-icon-dark.svg" alt="Logo" class="h-7 w-7 dark:hidden" />
    <img src="/anonyfiles-icon-light.svg" alt="Logo" class="h-7 w-7 hidden dark:inline" />
  </div>

  <!-- Titre centré (positionné via absolute) -->
  <h1 class="absolute left-1/2 -translate-x-1/2 text-base sm:text-lg font-semibold tracking-wide">
    {title}
  </h1>

  <!-- Menu burger à droite en mode mobile -->
  <div class="w-7 h-7 flex items-center justify-end">
    {#if $sidebarState.isMobile}
      <button
        on:click={() => sidebarState.update(s => ({ ...s, showSidebar: !s.showSidebar }))}
        class="p-1 rounded hover:bg-zinc-800 focus:outline-none focus:ring-2 focus:ring-zinc-500"
        aria-label="Menu"
      >
        <svg class="h-6 w-6" viewBox="0 0 24 24" stroke="currentColor" fill="none">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M4 6h16M4 12h16M4 18h16"/>
        </svg>
      </button>
    {/if}
  </div>
</header>
