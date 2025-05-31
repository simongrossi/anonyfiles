<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  import { sidebarState } from '../stores/sidebarStore';

  export let activeTab: string = '';

  const dispatch = createEventDispatcher();

  const navItems = [
    { icon: "🕵️", label: "Anonymisation", key: "anonymizer" },
    { icon: "🔓", label: "Désanonymisation", key: "deanonymizer" },
    { icon: "🧵", label: "Log", key: "log" },
    { icon: "⚙️", label: "Configuration", key: "config" },
    { icon: "🆕", label: "Nouveautés", key: "releases" }, // <-- NOUVEAU (icône à adapter si besoin)
    { icon: "ℹ️", label: "À Propos", key: "about" }     // <-- NOUVEAU (icône à adapter si besoin)
  ];

  let isMobile = false;
  let showMobileMenu = false;

  onMount(() => {
    const checkScreen = () => {
      const mobile = window.innerWidth < 768; // Tailwind's 'md' breakpoint
      isMobile = mobile;
      sidebarState.update(state => ({ ...state, isMobile: mobile }));
    };
    checkScreen();
    window.addEventListener("resize", checkScreen);
    return () => window.removeEventListener("resize", checkScreen);
  });

  // Réagit aux changements de isMobile ou showMobileMenu pour mettre à jour l'état global de la sidebar
  $: sidebarState.update(state => ({
    ...state,
    showSidebar: isMobile ? showMobileMenu : true
  }));

  function closeMenu() {
    if (isMobile) showMobileMenu = false;
  }

  function selectTab(key: string) {
    dispatch('selectTab', key);
    closeMenu(); // Ferme le menu mobile après la sélection
  }
</script>

{#if isMobile}
  <button
    class="m-2 p-2 rounded-md bg-gray-800 text-white z-50 fixed top-2 left-2 shadow-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
    on:click={() => showMobileMenu = true}
    aria-label="Ouvrir le menu"
    aria-expanded={showMobileMenu}
  >
    <svg class="h-6 w-6" stroke="currentColor" fill="none" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  </button>
{/if}

{#if isMobile && showMobileMenu}
  <button
    type="button"
    class="fixed inset-0 bg-black bg-opacity-40 z-30"
    on:click={closeMenu}
    aria-label="Fermer le menu"
    tabindex="-1"
  ></button>
{/if}

<nav class={`bg-gray-900 text-white w-64 h-full flex flex-col fixed top-0 left-0 z-40
            shadow-lg 
            transition-transform duration-300 ease-in-out
            ${isMobile ? (showMobileMenu ? 'translate-x-0' : '-translate-x-full') : 'translate-x-0'}`}>
  
  <div class="p-4 pt-6 pb-4 text-center border-b border-gray-700">
    <h1 class="text-xl font-semibold">Anonyfiles</h1>
  </div>

  <div class="flex-grow overflow-y-auto"> {#each navItems as item (item.key)}
    <button
      on:click={() => selectTab(item.key)}
      type="button"
      class="flex items-center px-6 py-3 gap-3 w-full text-left text-gray-300 hover:bg-gray-700 hover:text-white transition-colors duration-150
            {activeTab === item.key ? 'bg-blue-600 text-white font-semibold border-l-4 border-blue-400' : 'border-l-4 border-transparent'}"
      aria-current={activeTab === item.key ? 'page' : undefined}
    >
      <span class="text-xl">{item.icon}</span>
      <span>{item.label}</span>
    </button>
  {/each}
  </div>

  <div class="p-4 border-t border-gray-700">
    </div>
</nav>