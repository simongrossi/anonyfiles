<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import FileDropZone from './FileDropZone.svelte';
  import CustomRulesManager from './CustomRulesManager.svelte';
  import AnonymizationOptions from './AnonymizationOptions.svelte';
  import {
    inputText,
    outputText,
    auditLog,
    mappingCSV,
    isLoading,
    errorMessage,
    inputLineCount, // AJOUTÉ : Importer le store pour le nombre de lignes en entrée
    inputCharCount  // AJOUTÉ : Importer le store pour le nombre de caractères en entrée
  } from '../stores/anonymizationStore';
  import { customReplacementRules } from '../stores/customRulesStore';
  import { runAnonymization } from '../utils/anonymize';
  import {
    fileType,
    fileName,
    hasHeader,
    xlsxFile,
    previewTable,
    previewHeaders,
    handleFile // handleFile est importé depuis useFileHandler
  } from '../utils/useFileHandler';
  import { createEventDispatcher } from 'svelte';

  import { currentJobId } from '$lib/stores/jobStore';
  import { deleteJobFiles } from '$lib/utils/jobService';

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

  // AJOUTÉ : Fonction pour mettre à jour les compteurs pour la saisie manuelle
  function updateInputCountsFromTextarea(currentText: string) {
    inputLineCount.set(currentText.split('\n').length);
    inputCharCount.set(currentText.length);
  }

  // AJOUTÉ : Réagir aux changements de $inputText pour mettre à jour les compteurs
  // Ceci est utile si $inputText peut être modifié par d'autres moyens que le on:input direct du textarea
  // (par exemple, par handleFile via useFileHandler.ts qui met à jour $inputText)
  $: if ($inputText) {
    updateInputCountsFromTextarea($inputText);
  } else { // Assurer la réinitialisation si $inputText devient vide
    inputLineCount.set(0);
    inputCharCount.set(0);
  }


  $: canAnonymize =
    ($fileType === "txt" && $inputText.trim().length > 0) ||
    ($fileType === "csv" && $inputText.trim().length > 0) || // Pour CSV, on se base sur inputText qui est rempli par useFileHandler
    ($fileType === "xlsx" && $xlsxFile !== null) ||
    (["docx", "pdf", "json"].includes($fileType) && $fileName.length > 0); // json est aussi traité comme texte par useFileHandler

  let dragActive = false;
  const dataAnonymizerDropZoneId = "data-anonymizer-dropzone";

  function handleDragOver(event: Event) {
    const dragEvent = event as DragEvent;
    dragEvent.preventDefault();
    dragActive = true;
  }

  function handleDragLeave(event: Event) {
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
      // errorMessage.set(e.message || 'Une erreur inattendue est survenue.');
    }
  }

  function resetAll() {
    inputText.set("");
    inputLineCount.set(0); // AJOUTÉ : Réinitialiser le compteur de lignes
    inputCharCount.set(0); // AJOUTÉ : Réinitialiser le compteur de caractères
    outputText.set("");
    // outputLineCount.set(0); // Sera fait dans anonymize.ts lors de la réinitialisation de outputText
    // outputCharCount.set(0); // Idem
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
    currentJobId.set(null);
    dispatch("resetRequested");
  }

  async function handleDeleteCurrentJob() {
    const jobIdToDelele = get(currentJobId);
    if (jobIdToDelele) {
      const success = await deleteJobFiles(jobIdToDelele);
      if (success) {
        resetAll();
      }
    } else {
      console.warn("Tentative de suppression sans currentJobId");
    }
  }
</script>

{#if $isLoading}
  <div class="fixed inset-0 z-50 bg-black bg-opacity-40 flex flex-col items-center justify-center">
    <div class="flex flex-col items-center gap-3 p-8 bg-white dark:bg-zinc-800 rounded-2xl shadow-xl border border-zinc-200 dark:border-zinc-700">
      <svg class="animate-spin h-8 w-8 text-blue-700 dark:text-blue-500 mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
      </svg>
      <span class="font-bold text-lg text-zinc-800 dark:text-zinc-100 text-center">Anonymisation en cours…</span>
      <span class="text-zinc-500 dark:text-zinc-400 text-sm text-center max-w-xs">Merci de patienter pendant le traitement.</span>
    </div>
  </div>
{/if}

<div class="w-full max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
  <FileDropZone
    dropZoneId={dataAnonymizerDropZoneId}
    on:file={(event) => handleFile(event.detail.file)} on:dragover={handleDragOver}
    on:dragleave={handleDragLeave}
  />

  <div class="mb-4 flex flex-col h-[40vh] sm:h-[30vh]">
    <label for="inputText" class="font-semibold text-base text-zinc-700 dark:text-zinc-200 mb-1">Texte à anonymiser :</label>
    <textarea
      id="inputText"
      class="input-text flex-grow resize-none border rounded p-2 w-full overflow-y-auto"
      placeholder="Collez ou saisissez votre texte ici..."
      bind:value={$inputText}
      on:input={(e) => updateInputCountsFromTextarea(e.currentTarget.value)}
    ></textarea>
    <div class="text-xs text-gray-500 dark:text-gray-400 mt-1 text-right">
      Lignes: {$inputLineCount} | Caractères: {$inputCharCount}
    </div>
  </div>

  {#if $fileType === "csv" || $fileType === "xlsx"}
    <div class="mb-4 flex items-center gap-2">
      <input
        type="checkbox"
        id="hasHeader"
        bind:checked={$hasHeader}
        class="accent-blue-600 dark:accent-blue-400 h-4 w-4 rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500 dark:focus:ring-blue-500"
      />
      <label for="hasHeader" class="text-zinc-700 dark:text-zinc-200">Le fichier contient une ligne d’en-tête</label>
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

  {#if $outputText.trim().length > 0 || $errorMessage.trim().length > 0 || $isLoading}
    {#await import('./ResultView.svelte') then ResultViewModule}
      <div class="mt-6">
        <svelte:component this={ResultViewModule.default} />
        
        {#if $currentJobId && !$isLoading}
          <div class="mt-4 pt-4 border-t border-zinc-200 dark:border-zinc-700 flex justify-center">
            <button
              class="btn-secondary bg-red-500 hover:bg-red-600 dark:bg-red-600 dark:hover:bg-red-700 text-white border-red-500 hover:border-red-600 dark:border-red-600 dark:hover:border-red-700"
              on:click={handleDeleteCurrentJob}
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 16 16" class="w-4 h-4 mr-2 inline-block align-text-bottom">
                <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z"/>
                <path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4zM2.5 3h11V2h-11z"/>
              </svg>
              Supprimer les Fichiers du Job Traité
            </button>
          </div>
        {/if}
      </div>
    {/await}
  {/if}

  {#if $errorMessage && !$isLoading}
    <div class="card-panel card-error mt-4">
      <strong>Erreur (Anonymisation) :</strong>
      <pre class="whitespace-pre-wrap text-xs">{$errorMessage}</pre>
    </div>
  {/if}
</div>