<script lang="ts">
  import Dropzone from './Dropzone.svelte';

  let anonymizedFile: File | null = null;
  let mappingCsvFile: File | null = null;

  function handleAnonymizedDrop(files) {
    anonymizedFile = files[0];
  }
  function handleMappingDrop(files) {
    mappingCsvFile = files[0];
  }

  function reset() {
    anonymizedFile = null;
    mappingCsvFile = null;
  }

  function deanonymize() {
    // Appel API ou logique de désanonymisation
  }
</script>

<div class="p-10 flex flex-col items-center">
  <div class="bg-white rounded-2xl shadow-xl p-8 w-full max-w-xl">
    <h2 class="text-2xl font-bold mb-2 text-blue-900 flex items-center gap-2">
      <span>🔓</span>Désanonymiser un fichier
    </h2>
    <div class="mb-4">
      <Dropzone
        label="Déposez ici le fichier anonymisé (.txt, .csv, ...)"
        accept=".txt,.csv"
        onDrop={handleAnonymizedDrop}
      />
      {#if anonymizedFile}
        <div class="text-xs text-blue-700 mt-1">{anonymizedFile.name}</div>
      {/if}
    </div>
    <div class="mb-4">
      <Dropzone
        label="Déposez ici le mapping CSV"
        accept=".csv"
        onDrop={handleMappingDrop}
      />
      {#if mappingCsvFile}
        <div class="text-xs text-blue-700 mt-1">{mappingCsvFile.name}</div>
      {/if}
    </div>
    <div class="flex gap-3 mt-4">
      <button
        class="bg-blue-600 text-white font-semibold rounded-lg px-5 py-2 hover:bg-blue-700 disabled:bg-blue-300 transition"
        disabled={!anonymizedFile || !mappingCsvFile}
        on:click={deanonymize}
      >Désanonymiser</button>
      <button
        class="bg-zinc-200 text-zinc-800 rounded-lg px-4 py-2 hover:bg-zinc-300 transition"
        on:click={reset}
      >Réinitialiser</button>
    </div>
  </div>
</div>
