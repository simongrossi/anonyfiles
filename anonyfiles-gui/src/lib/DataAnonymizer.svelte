<script lang="ts">
  import CsvPreview from './CsvPreview.svelte';
  import XlsxPreview from './XlsxPreview.svelte';
  import CustomRulesManager from './CustomRulesManager.svelte';
  import { onMount } from 'svelte';

  let inputText = "";
  let outputText = "";
  let isLoading = false;
  let errorMessage = "";
  let fileType = "txt";
  let fileName = "";
  let hasHeader = true;
  let dragActive = false;
  let xlsxFile: File | null = null;

  // Audit log
  let auditLog: {
    pattern: string,
    replacement: string,
    type: string,
    count: number
  }[] = [];

  // Custom rules state
  let customReplacementRules: { pattern: string, replacement: string, isRegex?: boolean }[] = [];
  let customRuleError = "";

  // Détection mode bureau (Tauri) ou web
  let isTauri = false;
  onMount(() => {
      isTauri = typeof window !== 'undefined' && !!(window as any).__TAURI__;
  });

  let options = [
      { key: 'anonymizePersons', label: 'Personnes (PER)', default: true },
      { key: 'anonymizeLocations', label: 'Lieux (LOC)', default: true },
      { key: 'anonymizeOrgs', label: 'Organisations (ORG)', default: true },
      { key: 'anonymizeEmails', label: 'Emails', default: true },
      { key: 'anonymizeDates', label: 'Dates', default: true }
  ];
  let selected: { [key: string]: boolean } = {};
  options.forEach(opt => selected[opt.key] = opt.default);

  // UX copy/export output
  let copied = false;
  async function copyOutput() {
      try {
          await navigator.clipboard.writeText(outputText);
          copied = true;
          setTimeout(() => copied = false, 1200);
      } catch (e) {
          alert("Impossible de copier le texte. Vérifiez les permissions.");
      }
  }

  function exportOutput() {
      const blob = new Blob([outputText], { type: "text/plain;charset=utf-8" });
      const baseName = fileName ? fileName.replace(/\.[^/.]+$/, "") : "anonymized";
      const link = document.createElement("a");
      link.download = `${baseName}_anonymized.txt`;
      link.href = URL.createObjectURL(blob);
      document.body.appendChild(link);
      link.click();
      setTimeout(() => {
          URL.revokeObjectURL(link.href);
          document.body.removeChild(link);
      }, 200);
  }

  // Preview logic
  $: canAnonymize =
      (fileType === "txt" && inputText.trim().length > 0) ||
      (fileType === "csv" && inputText.trim().length > 0) ||
      (fileType === "xlsx" && xlsxFile !== null) ||
      (['docx', 'pdf', 'json'].includes(fileType) && fileName.length > 0);

  let previewTable: string[][] = [];
  let previewHeaders: string[] = [];
  const PREVIEW_ROW_LIMIT = 10;

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

  // File handlers
  function handleDrop(event: DragEvent) {
      event.preventDefault();
      dragActive = false;
      const file = event.dataTransfer?.files?.[0];
      if (file) {
          handleFile(file);
      }
  }
  function handleDragOver(event: DragEvent) {
      event.preventDefault();
      dragActive = true;
  }
  function handleDragLeave(event: DragEvent) {
      event.preventDefault();
      dragActive = false;
  }
  function handleFileInput(event: Event) {
      const input = event.target as HTMLInputElement;
      const file = input.files?.[0];
      if (file) {
          handleFile(file);
      }
  }
  function handleFile(file: File) {
      if (!file) return;
      inputText = "";
      outputText = "";
      errorMessage = "";
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
              inputText = content;
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
          errorMessage = `Format de fichier non pris en charge : ${ext}. Seuls les fichiers .txt, .csv, .xlsx, .docx, .pdf, .json sont acceptés.`;
          fileName = "";
          fileType = "txt";
      }
  }

  // Règles custom
  function handleAddCustomRule(event: CustomEvent<{ pattern: string, replacement: string, isRegex?: boolean }>) {
      const { pattern, replacement, isRegex } = event.detail;
      if (!pattern.trim()) {
          customRuleError = "Le motif de recherche ne peut pas être vide.";
          return;
      }
      if (customReplacementRules.some(r => r.pattern === pattern && r.replacement === replacement)) {
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

  // Fonctions utilitaires pour affichage du résumé d'audit
  function sIf(cond: boolean, suffix: string) {
    return cond ? suffix : '';
  }
  function totalReplacements() {
    return auditLog.reduce((acc, log) => acc + (log.count || 0), 0);
  }

  // Appel backend avec passage des customReplacementRules
  async function anonymize() {
      if (!canAnonymize) {
          errorMessage = "Veuillez glisser-déposer un fichier ou saisir du texte pour anonymiser.";
          return;
      }
      isLoading = true;
      outputText = "";
      errorMessage = "";
      auditLog = [];

      let configForBackend: { [key: string]: boolean } = {};
      options.forEach(opt => configForBackend[opt.key] = !!selected[opt.key]);
      let dataToSend: string | File | null = null;
      let currentInputFileName = fileName || (fileType === 'txt' ? 'input.txt' : `input.${fileType}`);

      if (inputText.trim().length > 0 && ['txt', 'csv', 'json'].includes(fileType)) {
          dataToSend = inputText;
      } else if (xlsxFile && fileType === 'xlsx') {
          dataToSend = xlsxFile;
      } else if (['docx', 'pdf'].includes(fileType) && fileName.length > 0) {
          dataToSend = null; // À compléter si gestion binaire plus tard
      } else {
          errorMessage = "Source de données invalide pour l'anonymisation.";
          isLoading = false;
          return;
      }

      if (isTauri) {
          // ... version Tauri à compléter si besoin ...
      } else {
          try {
              const API_URL = import.meta.env.VITE_ANONYFILES_API_URL || 'http://localhost:8000';
              const formData = new FormData();

              if (dataToSend instanceof File) {
                  formData.append('file', dataToSend, currentInputFileName);
              } else {
                  const blob = new Blob([dataToSend ?? ""], { type: 'text/plain;charset=utf-8' });
                  formData.append('file', blob, currentInputFileName);
              }
              formData.append('config_options', JSON.stringify({
                ...configForBackend,
                custom_replacement_rules: customReplacementRules
              }));
              formData.append('file_type', fileType);
              formData.append('has_header', String(hasHeader));

              const response = await fetch(`${API_URL}/anonymize/`, {
                  method: 'POST',
                  body: formData,
              });

              const data = await response.json();
              if (response.ok && data.status === 'success') {
                  outputText = data.anonymized_text;
                  auditLog = data.audit_log || [];
              } else {
                  errorMessage = data.message || data.detail || 'Erreur inconnue de l\'API Web.';
              }
          } catch (error: any) {
              errorMessage = `Erreur réseau ou du serveur : ${error.message}`;
          } finally {
              isLoading = false;
          }
      }
  }

  function resetAll() {
      inputText = "";
      outputText = "";
      fileName = "";
      fileType = "txt";
      errorMessage = "";
      hasHeader = true;
      previewTable = [];
      previewHeaders = [];
      xlsxFile = null;
      options.forEach(opt => selected[opt.key] = opt.default);
      dragActive = false;
      customReplacementRules = [];
      customRuleError = "";
      auditLog = [];
  }

  let showSplitView = true;
  let showOriginal = false;
</script>

{#if isLoading}
    <div class="fixed inset-0 z-50 bg-black bg-opacity-40 flex flex-col items-center justify-center">
        <div class="flex flex-col items-center gap-3 p-8 bg-white rounded-2xl shadow-xl border border-zinc-200">
            <svg class="animate-spin h-8 w-8 text-blue-700 mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
            </svg>
            <span class="font-bold text-lg text-zinc-800 text-center">
                Anonymisation en cours…
            </span>
            <span class="text-zinc-500 text-sm text-center max-w-xs">
                Pour les gros fichiers, le traitement peut prendre plusieurs secondes.<br/>
                Merci de patienter, la fenêtre reste responsive.
            </span>
        </div>
    </div>
{/if}

<div class="p-8">
    <h1 class="text-3xl font-bold text-zinc-800 dark:text-zinc-100">Anonyfiles</h1>
    <span class="text-zinc-400 text-xs mt-0 mb-7 block italic">
        Mode : {isTauri ? 'Application de bureau (Tauri)' : 'Application Web'}
    </span>

    <div
        class="w-full mb-6 border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center cursor-pointer transition bg-zinc-100 hover:bg-zinc-200 dark:bg-gray-700 dark:hover:bg-gray-600"
        class:bg-blue-50={dragActive}
        class:border-blue-500={dragActive}
        on:drop={handleDrop}
        on:dragover={handleDragOver}
        on:dragleave={handleDragLeave}
    >
        <input
            type="file"
            id="fileInput"
            accept=".txt,.csv,.xlsx,.docx,.pdf,.json"
            class="hidden"
            on:change={handleFileInput}
        />
        <label for="fileInput" class="cursor-pointer flex flex-col items-center gap-2">
            <span class="text-base font-medium text-zinc-700 dark:text-zinc-200">Déposez un fichier ou cliquez pour parcourir</span>
            <span class="text-sm text-zinc-500 dark:text-zinc-400">Formats supportés : .txt, .csv, .xlsx, .docx, .pdf, .json</span>
            {#if fileName}
                <span class="text-blue-800 font-semibold mt-2 dark:text-blue-400">{fileName}</span>
            {/if}
        </label>
    </div>

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
            class="w-full mt-2 p-3 border border-zinc-300 rounded-xl resize-y min-h-[90px] font-mono bg-white text-zinc-900 focus:bg-white transition dark:bg-gray-800 dark:text-zinc-100 dark:border-gray-600"
            placeholder="Collez ou saisissez votre texte ici..."
            bind:value={inputText}
            rows="4"
        ></textarea>
    </div>

    {#if fileType === "csv" || fileType === "xlsx"}
        <div class="mb-4 flex items-center gap-2">
            <input type="checkbox" id="hasHeader" bind:checked={hasHeader} class="accent-blue-600 dark:accent-blue-400" />
            <label for="hasHeader" class="select-none text-zinc-700 dark:text-zinc-200">Le fichier contient une ligne d’en-tête</label>
        </div>
    {/if}

    <div class="flex flex-wrap gap-5 mb-3 mt-1">
        {#each options as opt}
            <div class="flex items-center gap-2">
                <input
                    type="checkbox"
                    id={opt.key}
                    bind:checked={selected[opt.key]}
                    class="w-5 h-5 accent-blue-600 border-zinc-400 focus:ring-blue-400 bg-zinc-200 rounded dark:accent-blue-400 dark:bg-gray-700 dark:border-gray-500"
                    disabled={isLoading}
                />
                <label for={opt.key} class="select-none text-zinc-800 text-base font-medium dark:text-zinc-100">
                    {opt.label}
                </label>
            </div>
        {/each}
    </div>

    <h3 class="mt-4 mb-2 font-bold text-primary">Règles de remplacement personnalisées</h3>
    <CustomRulesManager
        currentRules={customReplacementRules}
        error={customRuleError}
        on:addrule={handleAddCustomRule}
        on:removerule={handleRemoveCustomRule}
    />

    <div class="flex gap-4 mt-2 mb-2">
        <button
            class="px-6 py-2 font-semibold text-white rounded-xl bg-blue-700 hover:bg-blue-800 active:bg-blue-900 shadow-sm transition-all disabled:bg-zinc-400 disabled:cursor-wait"
            on:click={anonymize}
            disabled={isLoading || !canAnonymize}
            aria-busy={isLoading}
        >
            {#if isLoading}
                <svg class="animate-spin h-5 w-5 mr-1 inline-block align-middle" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                </svg>
                Traitement en cours…
            {:else}
                Anonymiser
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
            <div class="flex items-center gap-4 mb-2">
                <span class="font-bold text-lg flex-1">
                    Aperçu {showSplitView ? "Avant / Après" : (showOriginal ? "Original" : "Anonymisé")}
                </span>
                <button
                    class="px-4 py-1 rounded-md bg-zinc-200 hover:bg-zinc-300 font-medium text-zinc-800 transition mr-2 dark:bg-gray-600 dark:hover:bg-gray-500 dark:text-zinc-100"
                    on:click={() => showSplitView = !showSplitView}
                    type="button"
                >
                    {showSplitView ? "Vue unique" : "Vue Avant/Après"}
                </button>
                {#if !showSplitView}
                    <button
                        class="px-3 py-1 rounded bg-blue-600 hover:bg-blue-700 text-white font-semibold ml-2"
                        on:click={() => showOriginal = !showOriginal}
                        type="button"
                    >
                        {showOriginal ? "Voir anonymisé" : "Voir original"}
                    </button>
                {/if}
            </div>
            <div class="flex gap-4">
                {#if showSplitView}
                    <div class="flex-1 flex flex-col gap-1">
                        <div class="font-medium text-zinc-700 text-xs mb-1 dark:text-zinc-200">Texte original</div>
                        <textarea readonly class="w-full min-h-[110px] max-h-60 p-2 border border-zinc-300 rounded-md font-mono text-xs resize-none bg-white dark:bg-gray-800 dark:border-gray-600 dark:text-zinc-100">{inputText}</textarea>
                    </div>
                    <div class="flex-1 flex flex-col gap-1">
                        <div class="font-medium text-zinc-700 text-xs mb-1 dark:text-zinc-200">Texte anonymisé</div>
                        <textarea readonly class="w-full min-h-[110px] max-h-60 p-2 border border-zinc-300 rounded-md font-mono text-xs resize-none bg-white dark:bg-gray-800 dark:border-gray-600 dark:text-zinc-100">{outputText}</textarea>
                    </div>
                {:else}
                    <div class="flex-1 flex flex-col gap-1">
                        <div class="font-medium text-zinc-700 text-xs mb-1 dark:text-zinc-200">
                            {showOriginal ? "Texte original" : "Texte anonymisé"}
                        </div>
                        <textarea readonly class="w-full min-h-[110px] max-h-60 p-2 border border-zinc-300 rounded-md font-mono text-xs resize-none bg-white dark:bg-gray-800 dark:border-gray-600 dark:text-zinc-100">
{showOriginal ? inputText : outputText}
                        </textarea>
                    </div>
                {/if}
            </div>
            <div class="flex justify-end gap-3 mt-2">
                <button on:click={copyOutput} class="px-4 py-1 rounded bg-blue-600 hover:bg-blue-700 text-white font-semibold">
                    {copied ? "✅ Copié !" : "Copier"}
                </button>
                <button on:click={exportOutput} class="px-4 py-1 rounded bg-green-600 hover:bg-green-700 text-white font-semibold">
                    Exporter
                </button>
            </div>
        </div>
    {/if}

    {#if errorMessage}
      <div class="bg-red-50 border border-red-300 text-red-800 px-4 py-3 mt-5 rounded-xl dark:bg-red-900 dark:border-red-700 dark:text-red-100">
        {errorMessage}
      </div>
    {/if}

    {#if auditLog.length}
      <div class="mt-6 p-4 rounded-xl bg-blue-50 border border-blue-200 dark:bg-blue-900 dark:border-blue-800">
        <div class="font-semibold text-blue-800 dark:text-blue-200 mb-2">Résumé des règles appliquées :</div>
        <!-- Compteur global -->
        <div class="mb-2 text-sm font-semibold text-blue-700 dark:text-blue-200">
          {totalReplacements()} remplacement{sIf(totalReplacements() > 1, 's')} au total
        </div>
        <ul class="space-y-1 text-blue-900 dark:text-blue-100 text-sm">
          {#each auditLog as log}
            <li>
              {log.pattern} → {log.replacement}
              <span class="ml-2 text-xs rounded bg-gray-200 dark:bg-gray-700 px-1">{log.type}</span>
              <span class="ml-2 text-xs text-gray-500">{log.count} remplacement{sIf(log.count > 1, 's')}</span>
            </li>
          {/each}
        </ul>
      </div>
    {/if}
</div>
