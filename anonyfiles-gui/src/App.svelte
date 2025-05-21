<script lang="ts">
  import DataAnonymizer from './lib/DataAnonymizer.svelte';
  import DeAnonymizer from './lib/DeAnonymizer.svelte';
  import ConfigurationView from './lib/ConfigurationView.svelte';

  let tab = 'anonymizer';
  const tabs = [
    { key: 'anonymizer', icon: '🕵️', label: 'Anonymisation' },
    { key: 'deanonymizer', icon: '🔓', label: 'Désanonymisation' },
    { key: 'config', icon: '⚙️', label: 'Configuration' }
  ];
</script>

<div class="flex h-screen">
  <nav class="w-56 bg-gray-800 text-white flex flex-col py-6 shadow-lg gap-2">
    {#each tabs as t}
      <button
        class="flex items-center gap-2 px-6 py-3 text-lg font-semibold text-left hover:bg-gray-700 transition rounded-xl focus:outline-none focus:ring-2 focus:ring-primary"
        class:font-bold={tab === t.key}
        class:bg-gray-700={tab === t.key}
        on:click={() => tab = t.key}
        aria-current={tab === t.key ? "page" : undefined}
      >
        <span>{t.icon}</span> {t.label}
      </button>
    {/each}
  </nav>
  <main class="flex-1 overflow-y-auto p-8">
    {#if tab === 'anonymizer'}
      <DataAnonymizer />
    {:else if tab === 'deanonymizer'}
      <DeAnonymizer />
    {:else if tab === 'config'}
      <ConfigurationView />
    {/if}
  </main>
</div>
