<!-- #anonyfiles/anonyfiles_gui/src/lib/components/Header.svelte -->
<script lang="ts">
  import { Menu, ShieldCheck } from 'lucide-svelte';
  import { sidebarState } from '../stores/sidebarStore';

  export let title: string = 'Anonyfiles';
</script>

<header
  class="w-full h-16 px-4 sm:px-6 flex items-center justify-between fixed top-0 z-50
         bg-zinc-950/95 backdrop-blur supports-[backdrop-filter]:bg-zinc-950/80
         text-white border-b border-zinc-800"
>
  <!-- Logo -->
  <div class="flex items-center gap-2 select-none" aria-label="Anonyfiles">
    <img src="/anonyfiles-icon-dark.svg" alt="" class="h-7 w-7 dark:hidden" />
    <img src="/anonyfiles-icon-light.svg" alt="" class="h-7 w-7 hidden dark:inline" />
    <span class="hidden sm:inline text-sm font-semibold tracking-tight text-zinc-200">
      Anonyfiles
    </span>
  </div>

  <!-- Titre -->
  <div
    class="absolute left-1/2 -translate-x-1/2 flex items-center gap-2 text-zinc-100 select-none"
  >
    <ShieldCheck size={18} class="text-brand-500" />
    <h1 class="text-base sm:text-lg font-semibold tracking-tight">{title}</h1>
  </div>

  <!-- Menu burger mobile -->
  <div class="w-7 h-7 flex items-center justify-end">
    {#if $sidebarState.isMobile}
      <button
        on:click={() => sidebarState.update((s) => ({ ...s, showSidebar: !s.showSidebar }))}
        class="p-1.5 rounded-lg hover:bg-zinc-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/50"
        aria-label="Menu"
      >
        <Menu size={20} />
      </button>
    {/if}
  </div>
</header>
