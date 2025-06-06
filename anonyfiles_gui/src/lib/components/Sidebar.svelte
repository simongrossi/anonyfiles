<!-- #anonyfiles/anonyfiles_gui/src/lib/components/Sidebar.svelte -->
<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  import { sidebarState } from '../stores/sidebarStore';

  export let activeTab: string = '';

  const dispatch = createEventDispatcher();

  const navItems = [
    { icon: "🕵️", label: "Anonymisation", key: "anonymizer" },
    { icon: "🔓", label: "Désanonymisation", key: "deanonymizer", wip: true },
    { icon: "🧵", label: "Log", key: "log" },
    { icon: "⚙️", label: "Configuration", key: "config" },
    { icon: "🆕", label: "Nouveautés", key: "releases" },
    { icon: "🧩", label: "Règles avancées", key: "replacementRules", wip: true },
    { icon: "ℹ️", label: "À Propos", key: "about" }
  ];

  let isMobile = false;
  let showMobileMenu = false;

  onMount(() => {
    const checkScreen = () => {
      const mobile = window.innerWidth < 768;
      isMobile = mobile;
      sidebarState.update(state => ({ ...state, isMobile: mobile }));
    };
    checkScreen();
    window.addEventListener("resize", checkScreen);
    return () => window.removeEventListener("resize", checkScreen);
  });

  $: sidebarState.update(state => ({
    ...state,
    showSidebar: isMobile ? showMobileMenu : true
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
    class="fixed inset-0 bg-black bg-opacity-40 z-30"
    on:click={closeMenu}
    aria-label="Fermer le menu"
    tabindex="-1"
  ></button>
{/if}

<nav class={`bg-zinc-900 text-white
  ${$sidebarState.isMobile ? 'w-16' : 'w-64'}
  h-[calc(100vh-4rem)] flex flex-col fixed top-16 left-0 z-40
  shadow-lg transition-all duration-300 ease-in-out
  ${$sidebarState.isMobile && !$sidebarState.showSidebar ? '-translate-x-full' : 'translate-x-0'}`}>

  <div class="flex-grow overflow-y-auto space-y-1 mt-2">
    {#each navItems as item (item.key)}
      <button
        on:click={() => selectTab(item.key)}
        type="button"
        title={item.label}
        class="relative group flex items-center px-4 py-3 gap-3 w-full text-left text-gray-300 hover:bg-gray-700 hover:text-white transition-colors duration-150
          {activeTab === item.key ? 'bg-blue-600 text-white font-semibold border-l-4 border-blue-400' : 'border-l-4 border-transparent'}"
        aria-current={activeTab === item.key ? 'page' : undefined}
      >
        <span class="text-xl">{item.icon}</span>
        {#if !$sidebarState.isMobile}
          <span class="whitespace-nowrap flex items-center gap-1">
            {item.label}
            {#if item.wip} <span class="text-yellow-400">🚧</span> {/if}
          </span>
        {/if}
      </button>
    {/each}
  </div>

  <div class="p-4 border-t border-zinc-800">
    {#if !$sidebarState.isMobile}
      <p class="text-xs text-gray-500">© 2025</p>
    {/if}
  </div>
</nav>
