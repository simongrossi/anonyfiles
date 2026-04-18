<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import { Sparkles, RotateCcw, Trash2, FileText, Loader2 } from 'lucide-svelte';
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
  import { debug, debugError } from '../utils/api';
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
      debugError("Erreur dans anonymisation:", e);
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
      debug("Tentative de suppression sans currentJobId");
    }
  }
</script>

{#if $isLoading}
  <div class="fixed inset-0 z-50 bg-zinc-900/50 backdrop-blur-sm flex flex-col items-center justify-center">
    <div class="flex flex-col items-center gap-3 p-8 bg-white dark:bg-zinc-800 rounded-2xl shadow-card-lg border border-zinc-200 dark:border-zinc-700">
      <Loader2 class="h-8 w-8 text-brand-600 dark:text-brand-100 animate-spin" />
      <span class="font-semibold text-lg text-zinc-800 dark:text-zinc-100 text-center">Anonymisation en cours…</span>
      <span class="text-zinc-500 dark:text-zinc-400 text-sm text-center max-w-xs">Merci de patienter pendant le traitement.</span>
    </div>
  </div>
{/if}

<div class="w-full max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 pb-10">

  <!-- Section 1 — Source -->
  <section class="ui-section mb-5">
    <header class="ui-section-header">
      <FileText size={16} class="text-zinc-400 dark:text-zinc-500" />
      <span class="ui-section-title">Source</span>
      <span class="ui-section-subtitle">&middot; fichier ou texte collé</span>
    </header>
    <div class="ui-section-body">
      <FileDropZone
        dropZoneId={dataAnonymizerDropZoneId}
        fileName={$fileName}
        on:file={(event) => handleFile(event.detail.file)}
        on:dragover={handleDragOver}
        on:dragleave={handleDragLeave}
        on:clear={() => {
          fileName.set('');
          fileType.set('txt');
          inputText.set('');
          xlsxFile.set(null);
          previewTable.set([]);
          previewHeaders.set([]);
        }}
      />

      <div class="flex items-center justify-between mb-1">
        <label for="inputText" class="ui-field-label !mb-0">Texte à anonymiser</label>
        <span class="text-[11px] text-zinc-400 dark:text-zinc-500 tabular-nums">
          {$inputLineCount} ligne{$inputLineCount > 1 ? 's' : ''} · {$inputCharCount} car.
        </span>
      </div>
      <textarea
        id="inputText"
        class="ui-textarea h-[28vh]"
        placeholder="Colle ou saisis ton texte ici…"
        bind:value={$inputText}
        on:input={(e) => updateInputCountsFromTextarea(e.currentTarget.value)}
      ></textarea>

      {#if $fileType === "csv" || $fileType === "xlsx"}
        <label class="mt-3 inline-flex items-center gap-2 cursor-pointer text-sm text-zinc-700 dark:text-zinc-200">
          <input
            type="checkbox"
            bind:checked={$hasHeader}
            class="h-4 w-4 rounded border-zinc-300 dark:border-zinc-600 text-brand-600 focus:ring-brand-500/40"
          />
          Le fichier contient une ligne d’en-tête
        </label>
      {/if}
    </div>
  </section>

  <!-- Section 2 — Entités -->
  <AnonymizationOptions {options} bind:selected isLoading={$isLoading} />

  <!-- Section 3 — Règles custom -->
  <CustomRulesManager />

  <!-- Barre d'actions -->
  <div class="sticky bottom-4 z-30 mt-6">
    <div class="flex flex-col sm:flex-row gap-2 justify-end rounded-2xl bg-white/80 dark:bg-zinc-800/80 backdrop-blur border border-zinc-200 dark:border-zinc-700 shadow-card px-4 py-3">
      <button
        type="button"
        class="ui-btn-secondary"
        on:click={resetAll}
        disabled={$isLoading}
      >
        <RotateCcw size={16} />
        Réinitialiser
      </button>
      <button
        type="button"
        class="ui-btn-primary"
        on:click={onClickAnonymize}
        disabled={$isLoading || !canAnonymize}
      >
        {#if $isLoading}
          <Loader2 size={16} class="animate-spin" />
          Traitement…
        {:else}
          <Sparkles size={16} />
          Anonymiser
        {/if}
      </button>
    </div>
  </div>

  {#if $outputText.trim().length > 0 || $errorMessage.trim().length > 0 || $isLoading}
    {#await import('./ResultView.svelte') then ResultViewModule}
      <div class="mt-6">
        <svelte:component this={ResultViewModule.default} />

        {#if $currentJobId && !$isLoading}
          <div class="mt-4 pt-4 border-t border-zinc-200 dark:border-zinc-700 flex justify-center">
            <button
              type="button"
              class="ui-btn-danger"
              on:click={handleDeleteCurrentJob}
            >
              <Trash2 size={16} />
              Supprimer les fichiers du job traité
            </button>
          </div>
        {/if}
      </div>
    {/await}
  {/if}

  {#if $errorMessage && !$isLoading}
    <div class="mt-4 rounded-2xl border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/30 text-red-800 dark:text-red-200 px-4 py-3">
      <strong class="font-semibold">Erreur (anonymisation)</strong>
      <pre class="whitespace-pre-wrap text-xs font-mono mt-1">{$errorMessage}</pre>
    </div>
  {/if}
</div>