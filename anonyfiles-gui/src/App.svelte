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
  <nav class="w-56 bg-gray-800 text-white flex flex-col justify-between py-6 shadow-lg">
    <div class="flex flex-col gap-2">
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
    </div>

    <a
      href="https://github.com/simongrossi/anonyfiles"
      target="_blank"
      rel="noopener noreferrer"
      class="flex justify-center mt-6"
      aria-label="Lien vers le dépôt GitHub"
    >
      <svg class="w-8 h-8 fill-white hover:fill-gray-300 transition" viewBox="0 0 24 24" aria-hidden="true">
        <path
          fill-rule="evenodd"
          clip-rule="evenodd"
          d="M12 0C5.37 0 0 5.373 0 12c0 5.303 3.438 9.8 8.205 11.387.6.113.82-.258.82-.577
          0-.285-.01-1.04-.015-2.04-3.338.725-4.042-1.614-4.042-1.614-.546-1.387-1.333-1.756-1.333-1.756-1.09-.745.083-.729.083-.729
          1.205.084 1.84 1.238 1.84 1.238 1.07 1.835 2.807 1.305 3.495.998.108-.775.42-1.305.763-1.605-2.665-.3-5.466-1.335-5.466-5.931
          0-1.31.468-2.382 1.235-3.222-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23a11.5 11.5 0 0 1 3-.405c1.02.005
          2.045.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.912
          1.23 3.222 0 4.61-2.805 5.625-5.475 5.92.435.375.825 1.096.825 2.22 0 1.606-.015 2.896-.015
          3.286 0 .315.21.69.825.57C20.565 21.795 24 17.295 24 12c0-6.627-5.373-12-12-12z"
        />
      </svg>
    </a>
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
