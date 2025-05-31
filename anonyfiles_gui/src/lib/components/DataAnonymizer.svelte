<!-- #anonyfiles/anonyfiles_gui/src/lib/components/DataAnonymizer.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import FileDropZone from './FileDropZone.svelte';
  import CustomRulesManager from './CustomRulesManager.svelte';
  import AnonymizationOptions from './AnonymizationOptions.svelte';
  import { inputText, outputText, auditLog, mappingCSV, isLoading, errorMessage } from '../stores/anonymizationStore';
  import { customReplacementRules } from '../stores/customRulesStore';
  import { runAnonymization } from '../utils/anonymize';
  import {
    fileType,
    fileName,
    hasHeader,
    xlsxFile,
    previewTable,
    previewHeaders,
    handleFile
  } from '../utils/useFileHandler';
  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher();

  let options = [
    { key: "anonymizePersons", label: "Personnes (PER)", default: false },
    { key: "anonymizeLocations", label: "Lieux (LOC)", default: false },
    { key: "anonymizeOrgs", label: "Organisations (ORG)", default: false },
    { key: "anonymizeEmails", label: "Emails", default: false },
    { key: "anonymizeDates", label: "Dates", default: false },
    { key: "anonymizeMisc", label: "MISC", default: false },
    { key: "anonymizePhones", label: "Téléphones (PHONE)", default: false },
    { key: "anonymizeIbans", label: "IBAN", default: false },
    { key: "anonymizeAddresses", label: "Adresses (ADDRESS)", default: false }
  ];

  let selected: { [key: string]: boolean } = {};
  options.forEach((opt) => (selected[opt.key] = opt.default));

  $: canAnonymize =
    ($fileType === "txt" && $inputText.trim().length > 0) ||
    ($fileType === "csv" && $inputText.trim().length > 0) ||
    ($fileType === "xlsx" && $xlsxFile !== null) ||
    (["docx", "pdf", "json"].includes($fileType) && $fileName.length > 0);

  let dragActive = false;

  function handleDragOver(event: DragEvent) {
    event.preventDefault();
    dragActive = true;
  }

  function handleDragLeave(event: DragEvent | CustomEvent) {
    const dragEvent = event instanceof DragEvent ? event : (event as any).detail?.event;
    if (dragEvent && typeof dragEvent.preventDefault === "function") {
      dragEvent.preventDefault();
    }
    dragActive = false;
  }

  async function onClickAnonymize() {
    try {
      await runAnonymization({
        fileType: $fileType,
        fileName: $fileName,
        hasHeader: $hasHeader,
        xlsxFile: $xlsxFile,
        selected,
        customReplacementRules: get(customReplacementRules)
      });
    } catch (e) {
      console.error("Erreur dans anonymisation:", e);
    }
  }

  function resetAll() {
    inputText.set("");
    outputText.set("");
    auditLog.set([]);
    mappingCSV.set("");
    errorMessage.set("");
    fileName.set("");
    fileType.set("txt");
    hasHeader.set(true);
    xlsxFile.set(null);
    previewTable.set([]);
    previewHeaders.set([]);
    options.forEach((opt) => (selected[opt.key] = opt.default));
    dragActive = false;
    customReplacementRules.set([]);
    dispatch("resetRequested");
  }
</script>

{#if $isLoading}
  <div class="fixed inset-0 z-50 bg-black bg-opacity-40 flex flex-col items-center justify-center">
    <div class="flex flex-col items-center gap-3 p-8 bg-white rounded-2xl shadow-xl border border-zinc-200">
      <svg class="animate-spin h-8 w-8 text-blue-700 mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
      </svg>
      <span class="font-bold text-lg text-zinc-800 text-center">Anonymisation en cours…</span>
      <span class="text-zinc-500 text-sm text-center max-w-xs">Merci de patienter pendant le traitement.</span>
    </div>
  </div>
{/if}

<div class="w-full max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
  <FileDropZone
    on:dragleave={(e) => handleDragLeave(e.detail?.event ?? e)}
    {dragActive}
    on:file={(event) => handleFile(event.detail.file)}
    on:dragover={handleDragOver}
    on:dragleave={handleDragLeave}
  />

  <div class="mb-4 flex flex-col h-[40vh] sm:h-[30vh]">
    <label for="inputText" class="font-semibold text-base text-zinc-700 dark:text-zinc-200 mb-1">Texte à anonymiser :</label>
    <textarea
      id="inputText"
      class="input-text flex-grow resize-none border rounded p-2 w-full overflow-y-auto"
      placeholder="Collez ou saisissez votre texte ici..."
      bind:value={$inputText}
    ></textarea>
  </div>

  {#if $fileType === "csv" || $fileType === "xlsx"}
    <div class="mb-4 flex items-center gap-2">
      <input
        type="checkbox"
        id="hasHeader"
        bind:checked={$hasHeader}
        class="accent-blue-600 dark:accent-blue-400"
      />
      <label for="hasHeader">Le fichier contient une ligne d’en-tête</label>
    </div>
  {/if}

  <AnonymizationOptions {options} bind:selected isLoading={$isLoading} />

  <CustomRulesManager />

  <div class="flex flex-col sm:flex-row gap-2 justify-center mt-4">
    <button class="btn-primary" on:click={onClickAnonymize} disabled={$isLoading || !canAnonymize}>
      {#if $isLoading}
        <svg class="animate-spin h-5 w-5 mr-1 inline-block align-middle" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
        </svg>
        Traitement…
      {:else}
        Anonymiser
      {/if}
    </button>
    <button class="btn-secondary" type="button" on:click={resetAll} disabled={$isLoading}>Réinitialiser</button>
  </div>

  {#if $outputText.trim().length > 0 || $isLoading}
    {#await import('./ResultView.svelte') then ResultViewModule}
      <svelte:component this={ResultViewModule.default} />
    {/await}
  {/if}

  {#if $errorMessage}
    <div class="card-panel card-error mt-4">
      <strong>Erreur :</strong>
      <pre class="whitespace-pre-wrap text-xs">{$errorMessage}</pre>
    </div>
  {/if}
</div>
