<!-- #anonyfiles/anonyfiles_gui/src/lib/components/Sidebar.svelte -->
<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  import { sidebarState } from '../stores/sidebarStore';

  export let activeTab: string = '';

  const dispatch = createEventDispatcher();

  const navItems = [
    { icon: "🕵️", label: "Anonymisation", key: "anonymizer" },
    { icon: "🔓", label: "Désanonymisation", key: "deanonymizer" },
    { icon: "🧵", label: "Log", key: "log" },
    { icon: "⚙️", label: "Configuration", key: "config" }
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

<!-- Bouton menu mobile -->
{#if isMobile}
  <button
    class="m-2 p-2 rounded-md bg-gray-800 text-white z-50 fixed top-2 left-2 shadow-md"
    on:click={() => showMobileMenu = true}
    aria-label="Ouvrir le menu"
  >
    ☰
  </button>
{/if}

<!-- Fond clicable accessible -->
{#if isMobile && showMobileMenu}
  <button
    type="button"
    class="fixed inset-0 bg-black bg-opacity-40 z-30"
    on:click={closeMenu}
    aria-label="Fermer le menu"
  ></button>
{/if}

<!-- Sidebar -->
<nav class={`bg-gray-900 text-white w-64 h-full flex flex-col fixed top-0 left-0 z-40
              transition-transform duration-300 ease-in-out
              ${isMobile ? (showMobileMenu ? 'translate-x-0' : '-translate-x-full') : 'translate-x-0'}`}>
  {#each navItems as item}
    <button
      on:click={() => selectTab(item.key)}
      type="button"
      class="flex items-center px-6 py-4 gap-2 w-full text-left hover:bg-gray-700 transition-colors
             {activeTab === item.key ? 'bg-blue-600 font-semibold' : ''}"
    >
      <span>{item.icon}</span>
      <span>{item.label}</span>
    </button>
  {/each}
</nav>
