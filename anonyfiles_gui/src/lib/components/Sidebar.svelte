<!-- #anonyfiles/anonyfiles_gui/src/lib/components/Sidebar.svelte -->
<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  import { sidebarState } from '../stores/sidebarStore';
  import {
    ShieldCheck,
    Unlock,
    ScrollText,
    Settings2,
    Sparkles,
    Puzzle,
    Info,
  } from 'lucide-svelte';

  export let activeTab: string = '';

  const dispatch = createEventDispatcher();

  type Item = {
    icon: typeof ShieldCheck;
    label: string;
    key: string;
    beta?: boolean;
  };
  const navItems: Item[] = [
    { icon: ShieldCheck, label: 'Anonymisation', key: 'anonymizer' },
    { icon: Unlock, label: 'Désanonymisation', key: 'deanonymizer', beta: true },
    { icon: ScrollText, label: 'Log', key: 'log' },
    { icon: Settings2, label: 'Configuration', key: 'config' },
    { icon: Sparkles, label: 'Nouveautés', key: 'releases' },
    { icon: Puzzle, label: 'Règles avancées', key: 'replacementRules', beta: true },
    { icon: Info, label: 'À Propos', key: 'about' },
  ];

  let isMobile = false;
  let showMobileMenu = false;

  onMount(() => {
    const checkScreen = () => {
      const mobile = window.innerWidth < 768;
      isMobile = mobile;
      sidebarState.update((state) => ({ ...state, isMobile: mobile }));
    };
    checkScreen();
    window.addEventListener('resize', checkScreen);
    return () => window.removeEventListener('resize', checkScreen);
  });

  $: sidebarState.update((state) => ({
    ...state,
    showSidebar: isMobile ? showMobileMenu : true,
  }));

  function closeMenu() {
    if (isMobile) showMobileMenu = false;
  }

  function selectTab(key: string) {
    dispatch('selectTab', key);
    closeMenu();
  }
</script>

{#if isMobile && showMobileMenu}
  <button
    type="button"
    class="fixed inset-0 bg-black/40 backdrop-blur-sm z-30"
    on:click={closeMenu}
    aria-label="Fermer le menu"
    tabindex="-1"
  ></button>
{/if}

<nav
  class={`bg-zinc-950 text-zinc-300 border-r border-zinc-800
    ${$sidebarState.isMobile ? 'w-16' : 'w-64'}
    h-[calc(100vh-4rem)] flex flex-col fixed top-16 left-0 z-40
    transition-all duration-300 ease-in-out
    ${$sidebarState.isMobile && !$sidebarState.showSidebar ? '-translate-x-full' : 'translate-x-0'}`}
>
  <div class="flex-grow overflow-y-auto py-3 px-2 space-y-0.5">
    {#each navItems as item (item.key)}
      {@const Icon = item.icon}
      {@const isActive = activeTab === item.key}
      <button
        on:click={() => selectTab(item.key)}
        type="button"
        title={item.label}
        class="group relative flex items-center gap-3 w-full rounded-lg px-3 py-2 text-sm text-left transition-colors
               {isActive
                 ? 'bg-brand-600/20 text-white shadow-inner'
                 : 'text-zinc-400 hover:bg-zinc-800/60 hover:text-zinc-100'}"
        aria-current={isActive ? 'page' : undefined}
      >
        {#if isActive}
          <span class="absolute left-0 top-1.5 bottom-1.5 w-0.5 rounded-r bg-brand-500"></span>
        {/if}
        <Icon size={18} strokeWidth={isActive ? 2.25 : 1.75} class="shrink-0" />
        {#if !$sidebarState.isMobile}
          <span class="flex-1 min-w-0 truncate text-left font-medium">{item.label}</span>
          {#if item.beta}
            <span class="shrink-0 text-[10px] uppercase tracking-wider font-semibold px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
              Beta
            </span>
          {/if}
        {/if}
      </button>
    {/each}
  </div>

  {#if !$sidebarState.isMobile}
    <div class="px-4 py-3 border-t border-zinc-800/80 text-[11px] text-zinc-500">
      Anonyfiles · © 2025
    </div>
  {/if}
</nav>
