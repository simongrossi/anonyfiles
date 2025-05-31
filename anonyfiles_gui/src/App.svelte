<!-- #anonyfiles/anonyfiles_gui/src/App.svelte -->
<script lang="ts">
  import DataAnonymizer from './lib/components/DataAnonymizer.svelte';
  import DeAnonymizer from './lib/components/DeAnonymizer.svelte';
  import ConfigurationView from './lib/components/ConfigurationView.svelte';
  import LogView from './lib/components/LogView.svelte';
  import ReleasesView from './lib/components/ReleasesView.svelte';
  import AboutView from './lib/components/AboutView.svelte';
  import Sidebar from './lib/components/Sidebar.svelte';
  import { sidebarState } from './lib/stores/sidebarStore';
  import { inputText, outputText, auditLog } from './lib/stores/anonymizationStore';
  import { derived } from 'svelte/store';
  import tauriLogo from './assets/tauri.svg';

  let tab = 'anonymizer';

  const mainMarginClass = derived(sidebarState, ({ isMobile, showSidebar }) =>
    isMobile || !showSidebar ? '' : 'md:ml-64'
  );

  function handleShowLog() {
    tab = 'log';
  }

  function handleReset() {
    inputText.set('');
    outputText.set('');
    auditLog.set([]);
  }
</script>

<div class="flex h-screen bg-zinc-50 dark:bg-zinc-900">
  <Sidebar activeTab={tab} on:selectTab={(e) => tab = e.detail} />

  <main class={`overflow-y-auto flex-1 transition-all duration-300 p-4 ${$mainMarginClass}`}>
    <div class="mx-auto max-w-7xl w-full">
      {#if tab === 'anonymizer'}
        <DataAnonymizer on:showLog={handleShowLog} on:resetRequested={handleReset} />
      {:else if tab === 'deanonymizer'}
        <DeAnonymizer />
      {:else if tab === 'log'}
        <LogView />
      {:else if tab === 'config'}
        <ConfigurationView />
      {:else if tab === 'releases'}
        <ReleasesView />
      {:else if tab === 'about'}
        <AboutView />
      {/if}

      <div class="flex items-center justify-center gap-4 mt-8 p-2 rounded-xl">
        <a
          href="https://github.com/simongrossi/anonyfiles"
          class="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition p-1 rounded"
          target="_blank"
          rel="noopener noreferrer"
          aria-label="Voir le projet sur GitHub"
          title="GitHub"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24" class="w-7 h-7">
            <path d="M12 2C6.48 2 2 6.58 2 12.26c0 4.5 2.87 8.31 6.84 9.66.5.09.68-.22.68-.48 0-.24-.01-.87-.01-1.7-2.78.62-3.37-1.36-3.37-1.36-.45-1.18-1.11-1.5-1.11-1.5-.91-.64.07-.63.07-.63 1.01.07 1.54 1.06 1.54 1.06 .89 1.56 2.34 1.11 2.91.85.09-.66.35-1.11.63-1.37-2.22-.26-4.56-1.14-4.56-5.06 0-1.12.39-2.04 1.02-2.76-.1-.26-.45-1.31.1-2.73 0 0 .84-.28 2.75 1.05a9.25 9.25 0 0 1 5 0c1.91-1.33 2.75-1.05 2.75-1.05 .55 1.42.2 2.47.1 2.73 .63.72 1.02 1.64 1.02 2.76 0 3.93-2.34 4.8-4.57 5.05 .36.31.68.92.68 1.86 0 1.35-.01 2.43-.01 2.76 0 .27.18.58.69.48A10.02 10.02 0 0 0 22 12.26C22 6.58 17.52 2 12 2z"/>
          </svg>
        </a>
        <a
          href="https://svelte.dev"
          target="_blank"
          rel="noopener noreferrer"
          class="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition p-1 rounded"
          aria-label="Svelte"
          title="Svelte"
        >
          <img src="https://upload.wikimedia.org/wikipedia/commons/1/1b/Svelte_Logo.svg" alt="Svelte" class="h-7 w-auto" />
        </a>
        <a
          href="https://tauri.app"
          target="_blank"
          rel="noopener noreferrer"
          class="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition p-1 rounded"
          aria-label="Tauri"
          title="Tauri"
        >
          <img src={tauriLogo} alt="Tauri" class="h-7 w-auto" />
        </a>
      </div>
    </div>
  </main>
</div>
