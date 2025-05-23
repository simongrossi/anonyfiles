<script lang="ts">
  import FileDropZone from './FileDropZone.svelte';
  import { onMount } from 'svelte';

  let inputFile: File | null = null;
  let mappingFile: File | null = null;
  let outputText = "";
  let isLoading = false;
  let errorMessage = "";
  let report: any[] = [];
  let permissive = false;
  let jobId: string | null = null;
  let pollingInterval: any = null;

  function resetAll() {
    inputFile = null;
    mappingFile = null;
    outputText = "";
    errorMessage = "";
    report = [];
    isLoading = false;
    jobId = null;
    if (pollingInterval) clearInterval(pollingInterval);
  }

  function handleInputDrop(event) {
    const file = event.detail.file;
    if (file) inputFile = file;
  }

  function handleMappingDrop(event) {
    const file = event.detail.file;
    if (file) mappingFile = file;
  }

  async function deanonymize() {
    if (!inputFile || !mappingFile) {
      errorMessage = "Merci de déposer un fichier à désanonymiser ET un fichier de mapping.";
      return;
    }
    errorMessage = "";
    outputText = "";
    report = [];
    isLoading = true;
    jobId = null;
    if (pollingInterval) clearInterval(pollingInterval);

    try {
      const API_URL = import.meta.env.VITE_ANONYFILES_API_URL || 'http://localhost:8000';
      const formData = new FormData();
      formData.append('file', inputFile, inputFile.name);
      formData.append('mapping', mappingFile, mappingFile.name);
      formData.append('permissive', String(permissive));

      // Création du job
      const response = await fetch(`${API_URL}/api/deanonymize/`, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Erreur lors du lancement du job.");
      }
      jobId = data.job_id;
      if (!jobId) throw new Error("job_id absent de la réponse API");

      // Polling du statut
      pollingInterval = setInterval(async () => {
        const statusResp = await fetch(`${API_URL}/api/deanonymize_status/${jobId}`);
        const statusData = await statusResp.json();
        if (statusData.status === "finished") {
          clearInterval(pollingInterval);
          outputText = statusData.deanonymized_text;
          report = statusData.report || [];
          isLoading = false;
        } else if (statusData.status === "error") {
          clearInterval(pollingInterval);
          errorMessage = statusData.error || 'Erreur inconnue pendant la désanonymisation.';
          isLoading = false;
        }
        // Sinon pending...
      }, 1200);
    } catch (e: any) {
      errorMessage = e.message || "Erreur lors de la désanonymisation.";
      isLoading = false;
      if (pollingInterval) clearInterval(pollingInterval);
    }
  }
</script>

<div class="p-8">
  <h1 class="text-2xl font-bold text-zinc-800 dark:text-zinc-100">Désanonymiser un fichier</h1>

  <div class="mt-5 grid grid-cols-1 md:grid-cols-2 gap-4">
    <div>
      <FileDropZone
        fileName={inputFile ? inputFile.name : ""}
        dragActive={false}
        on:file={handleInputDrop}
      />
      {#if inputFile}
        <span class="text-blue-800 dark:text-blue-400">{inputFile.name}</span>
      {/if}
    </div>
    <div>
      <FileDropZone
        fileName={mappingFile ? mappingFile.name : ""}
        dragActive={false}
        on:file={handleMappingDrop}
      />
      {#if mappingFile}
        <span class="text-blue-800 dark:text-blue-400">{mappingFile.name}</span>
      {/if}
    </div>
  </div>

  <div class="flex items-center mt-4 mb-4 gap-2">
    <input
      type="checkbox"
      id="permissive"
      bind:checked={permissive}
      class="accent-blue-600 dark:accent-blue-400"
      disabled={isLoading}
    />
    <label for="permissive" class="text-zinc-700 dark:text-zinc-200 select-none">
      Mode permissif (tolérer les noms inconnus)
    </label>
  </div>

  <div class="flex gap-4 mt-2 mb-6">
    <button
      class="px-6 py-2 font-semibold text-white rounded-xl bg-blue-700 hover:bg-blue-800 active:bg-blue-900 shadow-sm transition-all disabled:bg-zinc-400 disabled:cursor-wait"
      on:click={deanonymize}
      disabled={isLoading || !inputFile || !mappingFile}
      aria-busy={isLoading}
    >
      {#if isLoading}
        <svg class="animate-spin h-5 w-5 mr-1 inline-block align-middle" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
        </svg>
        Traitement…
      {:else}
        Désanonymiser
      {/if}
    </button>
    <button
      class="px-5 py-2 rounded-lg border border-zinc-300 text-zinc-700 bg-zinc-100 hover:bg-zinc-200 transition dark:border-gray-600 dark:text-zinc-100 dark:bg-gray-700 dark:hover:bg-gray-600"
      type="button"
      on:click={resetAll}
      disabled={isLoading}
    >
      Réinitialiser
    </button>
  </div>

  {#if outputText}
    <div class="border border-green-200 bg-green-50 text-green-900 rounded-2xl p-4 flex flex-col gap-2 mt-4 shadow-sm dark:border-green-800 dark:bg-green-900 dark:text-green-200">
      <span class="font-bold text-lg">Fichier désanonymisé</span>
      <textarea
        class="bg-white text-zinc-900 p-3 rounded-xl resize-y min-h-[60px] border border-zinc-300 font-mono w-full dark:bg-gray-800 dark:text-zinc-100 dark:border-gray-600"
        readonly
        value={outputText}
        rows="8"
      />
    </div>
  {/if}

  {#if errorMessage}
    <div class="border border-red-200 bg-red-50 text-red-800 rounded-xl p-3 mt-4 dark:border-red-600 dark:bg-red-900 dark:text-red-300">
      <strong>Erreur lors de la désanonymisation :</strong>
      <pre class="whitespace-pre-wrap text-xs">{errorMessage}</pre>
    </div>
  {/if}

  {#if report.length}
    <div class="mt-6 p-4 rounded-xl bg-blue-50 border border-blue-200 dark:bg-blue-900 dark:border-blue-800">
      <div class="font-semibold text-blue-800 dark:text-blue-200 mb-2">Résumé du rapport :</div>
      <ul class="space-y-1 text-blue-900 dark:text-blue-100 text-sm">
        {#each report as log}
          <li>
            {log.code} → {log.original}
            <span class="ml-2 text-xs text-gray-500">{log.status}</span>
          </li>
        {/each}
      </ul>
    </div>
  {/if}
</div>
