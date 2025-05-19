<script lang="ts">
  import TextAnonymizer from './lib/TextAnonymizer.svelte';
  // Composant à créer pour la config visuelle, même si vide au début :
  import ConfigurationView from './lib/ConfigurationView.svelte';

  let tab = 'anonymizer'; // "anonymizer" ou "config"
</script>

<div class="flex h-screen bg-gray-50">
  <nav class="w-56 bg-gray-800 text-white flex flex-col py-6 shadow-lg">
    <button
      class="px-6 py-3 text-lg font-semibold text-left hover:bg-gray-700 transition"
      on:click={() => tab = 'anonymizer'}
      class:font-bold={tab === 'anonymizer'}
    >
      🕵️ Anonymisation
    </button>
    <button
      class="px-6 py-3 text-lg font-semibold text-left hover:bg-gray-700 transition"
      on:click={() => tab = 'config'}
      class:font-bold={tab === 'config'}
    >
      ⚙️ Configuration
    </button>
  </nav>
  <main class="flex-1 overflow-y-auto p-8">
    {#if tab === 'anonymizer'}
      <TextAnonymizer />
    {:else if tab === 'config'}
      <ConfigurationView />
    {/if}
  </main>
</div>

<style>
  :global(body) {
    margin: 0;
    font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  }
</style>
