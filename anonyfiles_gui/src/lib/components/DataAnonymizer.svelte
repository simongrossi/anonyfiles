<!-- #anonyfiles/anonyfiles_gui/src/lib/components/DataAnonymizer.svelte -->
<script lang="ts">
  import CsvPreview from './CsvPreview.svelte';
  import XlsxPreview from './XlsxPreview.svelte';
  import CustomRulesManager from './CustomRulesManager.svelte';
  import FileDropZone from './FileDropZone.svelte';
  import ResultView from './ResultView.svelte';
  import AnonymizationOptions from './AnonymizationOptions.svelte';
  import { inputText, outputText, auditLog, mappingCSV, isLoading, errorMessage } from '../stores/anonymizationStore';
  import { runAnonymization } from '../utils/anonymize';
  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher();

  let fileType = "txt";
  let fileName = "";
  let hasHeader = true;
  let dragActive = false;
  let xlsxFile: File | null = null;
  let previewTable: string[][] = [];
  let previewHeaders: string[] = [];
  const PREVIEW_ROW_LIMIT = 10;

  let customReplacementRules: { pattern: string, replacement: string, isRegex?: boolean }[] = [];
  let customRuleError = "";

  let options = [
    { key: 'anonymizePersons', label: 'Personnes (PER)', default: true },
    { key: 'anonymizeLocations', label: 'Lieux (LOC)', default: true },
    { key: 'anonymizeOrgs', label: 'Organisations (ORG)', default: true },
    { key: 'anonymizeEmails', label: 'Emails', default: true },
    { key: 'anonymizeDates', label: 'Dates', default: true }
  ];
  let selected: { [key: string]: boolean } = {};
  options.forEach(opt => selected[opt.key] = opt.default);

  $: canAnonymize =
    (fileType === "txt" && $inputText.trim().length > 0) ||
    (fileType === "csv" && $inputText.trim().length > 0) ||
    (fileType === "xlsx" && xlsxFile !== null) ||
    (['docx', 'pdf', 'json'].includes(fileType) && fileName.length > 0);

  function handleDragOver(event: DragEvent) {
    event.preventDefault();
    dragActive = true;
  }
  function handleDragLeave(event: DragEvent | CustomEvent) {
    const dragEvent = (event instanceof DragEvent) ? event : (event as any).detail?.event;
    if (dragEvent && typeof dragEvent.preventDefault === 'function') {
      dragEvent.preventDefault();
    }
    dragActive = false;
  }

  function parseCsvPreview(csvText: string) {
    const rows = csvText.trim().split(/\r?\n/);
    if (!rows.length) {
      previewHeaders = [];
      previewTable = [];
      return;
    }
    let delimiter = ",";
    if (rows[0].split(";").length > rows[0].split(",").length) delimiter = ";";
    previewHeaders = rows[0].split(delimiter);
    previewTable = rows.slice(1, 1 + PREVIEW_ROW_LIMIT).map(row => row.split(delimiter));
  }

  function handleFile(file: File) {
    if (!file) return;
    inputText.set('');
    outputText.set('');
    errorMessage.set('');
    previewTable = [];
    previewHeaders = [];
    xlsxFile = null;
    fileName = file.name;
    const ext = file.name.split('.').pop()?.toLowerCase() || "";
    fileType = ext;

    if (["txt", "csv", "json"].includes(ext)) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        inputText.set(content);
        if (ext === "csv") {
          parseCsvPreview(content);
        }
      };
      reader.readAsText(file, "UTF-8");
    } else if (["xlsx", "docx", "pdf"].includes(ext)) {
      if (ext === "xlsx") {
        xlsxFile = file;
      }
    } else {
      errorMessage.set(`Format de fichier non pris en charge : ${ext}. Seuls les fichiers .txt, .csv, .xlsx, .docx, .pdf, .json sont acceptés.`);
      fileName = "";
      fileType = "txt";
    }
  }

  function handleAddCustomRule(event: CustomEvent<{ pattern: string, replacement: string, isRegex?: boolean }>) {
    const { pattern, replacement, isRegex } = event.detail;
    if (!pattern.trim()) {
      customRuleError = "Le motif de recherche ne peut pas être vide.";
      return;
    }
    if (customReplacementRules.some(r => r.pattern === pattern && r.replacement === replacement && r.isRegex === isRegex)) {
      customRuleError = "Cette règle existe déjà.";
      return;
    }
    customReplacementRules = [...customReplacementRules, { pattern, replacement, isRegex }];
    customRuleError = "";
  }
  function handleRemoveCustomRule(event: CustomEvent<number>) {
    customReplacementRules = customReplacementRules.filter((_, i) => i !== event.detail);
    customRuleError = "";
  }

  async function onClickAnonymize() {
    try {
      await runAnonymization({
        fileType,
        fileName,
        hasHeader,
        xlsxFile,
        selected,
        customReplacementRules
      });
    } catch (e) {
      console.error("Erreur dans anonymisation:", e);
    }
  }

  function resetAll() {
    inputText.set('');
    outputText.set('');
    auditLog.set([]);
    mappingCSV.set('');
    errorMessage.set('');
    fileName = "";
    fileType = "txt";
    hasHeader = true;
    previewTable = [];
    previewHeaders = [];
    xlsxFile = null;
    options.forEach(opt => selected[opt.key] = opt.default);
    dragActive = false;
    customReplacementRules = [];
    customRuleError = "";
    dispatch('resetRequested');
  }
</script>

{#if $isLoading}
  <div class="fixed inset-0 z-50 bg-black bg-opacity-40 flex flex-col items-center justify-center">
    <div class="flex flex-col items-center gap-3 p-8 bg-white rounded-2xl shadow-xl border border-zinc-200">
      <svg class="animate-spin h-8 w-8 text-blue-700 mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
      </svg>
      <span class="font-bold text-lg text-zinc-800 text-center">Anonymisation en cours…</span>
      <span class="text-zinc-500 text-sm text-center max-w-xs">Pour les gros fichiers, le traitement peut prendre plusieurs secondes.<br/>Merci de patienter, la fenêtre reste responsive.</span>
    </div>
  </div>
{/if}

<div>
  <FileDropZone
    on:dragleave={e => handleDragLeave(e.detail?.event ?? e)}
    {dragActive}
    on:file={event => handleFile(event.detail.file)}
    on:dragover={handleDragOver}
    on:dragleave={handleDragLeave}
  />

  {#if fileType === "csv" && previewTable.length}
    <CsvPreview headers={previewHeaders} rows={previewTable} hasHeader={hasHeader} />
  {/if}

  {#if fileType === "xlsx" && xlsxFile}
    <XlsxPreview file={xlsxFile} hasHeader={hasHeader} />
  {/if}

  <div class="mb-4">
    <label for="inputText" class="font-semibold text-base text-zinc-700 dark:text-zinc-200">Texte à anonymiser :</label>
    <textarea
      id="inputText"
      class="input-text"
      placeholder="Collez ou saisissez votre texte ici..."
      bind:value={$inputText}
      rows="4"
    ></textarea>
  </div>

  {#if fileType === "csv" || fileType === "xlsx"}
    <div class="mb-4 flex items-center gap-2">
      <input type="checkbox" id="hasHeader" bind:checked={hasHeader} class="accent-blue-600 dark:accent-blue-400" />
      <label for="hasHeader" class="select-none text-zinc-700 dark:text-zinc-200">Le fichier contient une ligne d’en-tête</label>
    </div>
  {/if}

  <AnonymizationOptions {options} bind:selected isLoading={$isLoading} />

  <h3 class="mt-4 mb-2 font-bold text-primary">Règles de remplacement personnalisées</h3>
  <CustomRulesManager
    currentRules={customReplacementRules}
    error={customRuleError}
    on:addrule={handleAddCustomRule}
    on:removerule={handleRemoveCustomRule}
  />

  <div class="flex gap-4 mt-2 mb-2">
    <button class="btn-primary mr-2"
      on:click={onClickAnonymize}
      disabled={$isLoading || !canAnonymize}
      aria-busy={$isLoading}
    >
      {#if $isLoading}
        <svg class="animate-spin h-5 w-5 mr-1 inline-block align-middle" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
        </svg>
        Traitement en cours…
      {:else}
        Anonymiser
      {/if}
    </button>
    <button class="btn-secondary" type="button" on:click={resetAll} disabled={$isLoading}>
      Réinitialiser
    </button>
  </div>

  <ResultView />

  {#if $errorMessage}
    <div class="card-panel card-error mt-4">
      <strong>Erreur lors de l’anonymisation :</strong>
      <pre class="whitespace-pre-wrap text-xs">{$errorMessage}</pre>
    </div>
  {/if}
</div>
