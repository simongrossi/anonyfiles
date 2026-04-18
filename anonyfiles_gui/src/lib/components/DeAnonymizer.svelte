<script lang="ts">
  import FileDropZone from './FileDropZone.svelte';
  import { onDestroy } from 'svelte';
  import { apiUrl, pollJob, debug } from '$lib/utils/api';

  let inputFile: File | null = null;
  let mappingFile: File | null = null;
  let outputText: string = "";
  let isLoading: boolean = false;
  let errorMessage: string = "";
  let report: string[] = [];
  let permissive: boolean = false;
  let abortController: AbortController | null = null;

  function resetAll() {
    inputFile = null;
    mappingFile = null;
    outputText = "";
    errorMessage = "";
    report = [];
    isLoading = false;
    if (abortController) {
      abortController.abort();
      abortController = null;
    }
  }

  function handleFileDropped(event: CustomEvent<{ file: File; zoneId: string }>) {
    const file = event.detail?.file;
    const zoneIdFromEvent = event.detail?.zoneId;

    debug(`DeAnonymizer: Fichier reçu - Zone: '${zoneIdFromEvent}', Nom:`, file?.name);

    if (!file) {
      if (zoneIdFromEvent === 'input-file-zone') inputFile = null;
      if (zoneIdFromEvent === 'mapping-file-zone') mappingFile = null;
      return;
    }
    errorMessage = "";
    if (zoneIdFromEvent === 'input-file-zone') {
      inputFile = file;
    } else if (zoneIdFromEvent === 'mapping-file-zone') {
      if (file.type === 'text/csv' || file.name.toLowerCase().endsWith('.csv')) {
        mappingFile = file;
      } else {
        mappingFile = null;
        errorMessage = "Le fichier de mapping doit être un fichier .csv";
      }
    }
  }

  async function deanonymize() {
    if (!inputFile || !mappingFile) {
      errorMessage = "Merci de sélectionner un fichier à désanonymiser ET un fichier de mapping CSV.";
      isLoading = false;
      return;
    }

    errorMessage = "";
    outputText = "";
    report = [];
    isLoading = true;
    if (abortController) abortController.abort();
    abortController = new AbortController();
    const signal = abortController.signal;

    try {
      const formData = new FormData();
      formData.append('file', inputFile, inputFile.name);
      formData.append('mapping', mappingFile, mappingFile.name);
      formData.append('permissive', String(permissive));

      const deanonymizeEndpoint = await apiUrl('deanonymize/');
      debug("DeAnonymizer: Appel API:", deanonymizeEndpoint);

      const response = await fetch(deanonymizeEndpoint, { method: 'POST', body: formData, signal });
      const data = await response.json();

      if (!response.ok) throw new Error(data?.detail || data?.error || `Erreur HTTP ${response.status}`);

      const jobId = data.job_id;
      if (!jobId) throw new Error(data?.error || "job_id absent de la réponse API.");

      const statusData = await pollJob<{
        status: string;
        deanonymized_text?: string;
        audit_log?: string[];
        error?: string;
      }>(await apiUrl(`deanonymize_status/${jobId}`), { signal });

      outputText = statusData.deanonymized_text || "";
      report = statusData.audit_log || [];
      isLoading = false;
    } catch (e: any) {
      if (e?.name !== 'AbortError') {
        errorMessage = e.message || "Erreur lancement désanonymisation.";
      }
      isLoading = false;
    }
  }

  onDestroy(() => {
    if (abortController) abortController.abort();
  });
</script>


<div class="p-4 md:p-8">
  <h1 class="text-xl md:text-2xl font-bold text-zinc-800 dark:text-zinc-100 mb-6">
    Désanonymiser un Fichier
  </h1>

  <div class="mt-5 grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
    <div>
      <label for="deanonymize-input-file" class="block text-sm font-semibold mb-2 text-zinc-700 dark:text-zinc-300">📄 Fichier anonymisé à restaurer</label>
      <FileDropZone
        id="deanonymize-input-file"
        dropZoneId="input-file-zone"
        fileName={inputFile ? inputFile.name : ""}
        accept=".txt,.csv,.xlsx,.docx,.pdf,.json"
        on:file={handleFileDropped}
      />
      {#if inputFile}
        <p class="text-xs mt-1 text-blue-700 dark:text-blue-400">Fichier source : {inputFile.name}</p>
      {/if}
    </div>
    <div>
      <label for="deanonymize-mapping-file" class="block text-sm font-semibold mb-2 text-zinc-700 dark:text-zinc-300">📑 Fichier de mapping (CSV)</label>
      <FileDropZone
        id="deanonymize-mapping-file"
        dropZoneId="mapping-file-zone"
        fileName={mappingFile ? mappingFile.name : ""}
        accept=".csv"
        on:file={handleFileDropped}
      />
      {#if mappingFile}
        <p class="text-xs mt-1 text-blue-700 dark:text-blue-400">Fichier mapping : {mappingFile.name}</p>
      {/if}
    </div>
  </div>

  <div class="flex items-center mt-4 mb-6 gap-2">
    <input
      type="checkbox"
      id="permissiveToggleDeanonymize"
      bind:checked={permissive}
      class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:ring-offset-gray-800 dark:focus:ring-blue-600 accent-blue-600 dark:accent-blue-400"
      disabled={isLoading}
    />
    <label for="permissiveToggleDeanonymize" class="text-sm text-zinc-700 dark:text-zinc-200 select-none">
      Mode permissif
    </label>
  </div>

  <div class="flex flex-wrap gap-4 mt-2 mb-6">
    <button
      class="px-6 py-2 font-semibold text-white rounded-xl bg-blue-700 hover:bg-blue-800 active:bg-blue-900 shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      on:click={deanonymize}
      disabled={isLoading || !inputFile || !mappingFile}
      aria-busy={isLoading}
    >
      {#if isLoading}
        <svg class="animate-spin h-5 w-5 mr-2 inline-block align-middle" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
        Traitement…
      {:else}
        Désanonymiser
      {/if}
    </button>
    <button
      class="px-5 py-2 rounded-lg border border-zinc-300 text-zinc-700 bg-zinc-100 hover:bg-zinc-200 transition dark:border-gray-600 dark:text-zinc-100 dark:bg-gray-700 dark:hover:bg-gray-600 disabled:opacity-50"
      type="button"
      on:click={resetAll}
      disabled={isLoading}
    >
      Réinitialiser
    </button>
  </div>

  {#if errorMessage}
    <div class="border border-red-200 bg-red-50 text-red-800 rounded-xl p-4 mt-4 shadow-md dark:border-red-700 dark:bg-red-900/30 dark:text-red-300" role="alert">
      <strong class="font-semibold">Erreur :</strong>
      <pre class="mt-1 whitespace-pre-wrap text-sm font-mono">{typeof errorMessage === 'object' ? JSON.stringify(errorMessage, null, 2) : errorMessage}</pre>
    </div>
  {/if}

  {#if outputText}
    <div class="border border-green-200 bg-green-50 text-green-900 rounded-2xl p-4 flex flex-col gap-2 mt-4 shadow-sm dark:border-green-700 dark:bg-green-900/30 dark:text-green-200">
      <h3 class="font-bold text-lg">Fichier désanonymisé :</h3>
      <textarea
        class="w-full mt-1 p-3 border border-zinc-300 rounded-xl resize-y min-h-[120px] font-mono text-sm bg-white text-zinc-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-zinc-100 dark:border-gray-600 dark:focus:ring-blue-600 dark:focus:border-blue-600"
        readonly
        value={outputText}
        rows="10"
      ></textarea>
    </div>
  {/if}

  {#if report && report.length > 0}
    <div class="mt-6 p-4 rounded-xl bg-sky-50 border border-sky-200 dark:bg-sky-900/30 dark:border-sky-700">
      <h3 class="font-semibold text-sky-800 dark:text-sky-200 mb-2">Journal / Avertissements :</h3>
      <ul class="list-disc list-inside space-y-1 text-sky-900 dark:text-sky-100 text-sm">
        {#each report as message}
          <li>{typeof message === 'object' ? JSON.stringify(message) : message}</li>
        {/each}
      </ul>
    </div>
  {/if}
</div>