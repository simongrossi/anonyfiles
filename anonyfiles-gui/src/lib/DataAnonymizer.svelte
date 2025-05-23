<script lang="ts">
    import CsvPreview from './CsvPreview.svelte';
    import XlsxPreview from './XlsxPreview.svelte';
    import CustomRulesManager from './CustomRulesManager.svelte';
    import FileDropZone from './FileDropZone.svelte';
    import ResultView from './ResultView.svelte';
    import AnonymizationOptions from './AnonymizationOptions.svelte';
    import { onMount, createEventDispatcher } from 'svelte';

    const dispatch = createEventDispatcher();

    export let inputText: string = "";
    export let outputText: string = "";
    export let auditLog: any[] = [];

    let localInput = "";
    let localOutput = "";
    let localAuditLog = [];
    $: totalReplacements = localAuditLog.reduce((sum, log) => sum + (log.count || 0), 0);

    onMount(() => {
        localInput = inputText || "";
        localOutput = outputText || "";
        localAuditLog = auditLog || [];
    });

    let isLoading = false;
    let errorMessage = "";
    let fileType = "txt";
    let fileName = "";
    let hasHeader = true;
    let dragActive = false;
    let xlsxFile: File | null = null;

    let customReplacementRules: { pattern: string, replacement: string, isRegex?: boolean }[] = [];
    let customRuleError = "";

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

    let copied = false;
    async function copyOutput() {
        try {
            await navigator.clipboard.writeText(localOutput);
            copied = true;
            setTimeout(() => copied = false, 1200);
        } catch (e) {
            alert("Impossible de copier le texte. Vérifiez les permissions.");
        }
    }

    function exportOutput() {
        const blob = new Blob([localOutput], { type: "text/plain;charset=utf-8" });
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

    $: canAnonymize =
        (fileType === "txt" && localInput.trim().length > 0) ||
        (fileType === "csv" && localInput.trim().length > 0) ||
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

    // --- DRAG & DROP ET FICHIER ---
    function handleDragOver(event: DragEvent) {
        event.preventDefault();
        dragActive = true;
    }
    function handleDragLeave(event: DragEvent) {
        event.preventDefault();
        dragActive = false;
    }
    function handleFile(file: File) {
        if (!file) return;
        localInput = "";
        localOutput = "";
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
                localInput = content;
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

    let pollingInterval: any = null;

    async function anonymize() {
        if (!canAnonymize) {
            errorMessage = "Veuillez glisser-déposer un fichier ou saisir du texte pour anonymiser.";
            return;
        }
        isLoading = true;
        localOutput = "";
        errorMessage = "";
        localAuditLog = [];
        if (pollingInterval) clearInterval(pollingInterval);

        let configForBackend: { [key: string]: any } = {};
        options.forEach(opt => configForBackend[opt.key] = !!selected[opt.key]);
        configForBackend["custom_replacement_rules"] = customReplacementRules;

        // Ajoute ce log pour la vérification étape 1
        console.log("CONFIG ENVOYÉE AU BACKEND :", JSON.stringify(configForBackend, null, 2));

        let dataToSend: string | File | null = null;
        let currentInputFileName = fileName || (fileType === 'txt' ? 'input.txt' : `input.${fileType}`);

        if (localInput.trim().length > 0 && ['txt', 'csv', 'json'].includes(fileType)) {
            dataToSend = localInput;
        } else if (xlsxFile && fileType === 'xlsx') {
            dataToSend = xlsxFile;
        } else if (['docx', 'pdf'].includes(fileType) && fileName.length > 0) {
            dataToSend = null; // À compléter plus tard
        } else {
            errorMessage = "Source de données invalide pour l'anonymisation.";
            isLoading = false;
            return;
        }

        // *** MODIF ICI ***
        const API_URL = import.meta.env.VITE_ANONYFILES_API_URL;
        if (!API_URL) {
            errorMessage = "La variable d'environnement VITE_ANONYFILES_API_URL doit être définie !";
            isLoading = false;
            return;
        }
        // *** FIN MODIF ***

        try {
            const formData = new FormData();

            if (dataToSend instanceof File) {
                formData.append('file', dataToSend, currentInputFileName);
            } else {
                const blob = new Blob([dataToSend ?? ""], { type: 'text/plain;charset=utf-8' });
                formData.append('file', blob, currentInputFileName);
            }
            formData.append('config_options', JSON.stringify(configForBackend));
            formData.append('file_type', fileType);
            formData.append('has_header', String(hasHeader));

            const response = await fetch(`${API_URL}/api/anonymize/`, {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Erreur lors de la création du job.');
            }
            const jobId = data.job_id;
            if (!jobId) throw new Error("job_id absent de la réponse API");

            pollingInterval = setInterval(async () => {
                const statusResp = await fetch(`${API_URL}/api/anonymize_status/${jobId}`);
                const statusData = await statusResp.json();
                if (statusData.status === "finished") {
                    clearInterval(pollingInterval);
                    localOutput = statusData.anonymized_text;
                    localAuditLog = statusData.audit_log || [];
                    // --- ICI FORCAGE DE LA VUE ANONYMISÉE ---
                    showSplitView = false;
                    showOriginal = false;
                    isLoading = false;
                    dispatch('anonymizationComplete', {
                        inputText: localInput,
                        outputText: localOutput,
                        auditLog: localAuditLog
                    });
                } else if (statusData.status === "error") {
                    clearInterval(pollingInterval);
                    errorMessage = statusData.error || 'Erreur inconnue pendant l’anonymisation.';
                    isLoading = false;
                }
            }, 1200);

        } catch (error: any) {
            errorMessage = `Erreur réseau ou du serveur : ${error.message}`;
            isLoading = false;
            if (pollingInterval) clearInterval(pollingInterval);
        }
    }

    function resetAll() {
        localInput = "";
        localOutput = "";
        localAuditLog = [];
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
        if (pollingInterval) clearInterval(pollingInterval);
        dispatch('resetRequested');
    }

    let showSplitView = false;
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

<div>
  <FileDropZone
    {fileName}
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
          bind:value={localInput}
          rows="4"
      ></textarea>
  </div>

  {#if fileType === "csv" || fileType === "xlsx"}
      <div class="mb-4 flex items-center gap-2">
          <input type="checkbox" id="hasHeader" bind:checked={hasHeader} class="accent-blue-600 dark:accent-blue-400" />
          <label for="hasHeader" class="select-none text-zinc-700 dark:text-zinc-200">Le fichier contient une ligne d’en-tête</label>
      </div>
  {/if}

  <AnonymizationOptions {options} bind:selected {isLoading} />

  <h3 class="mt-4 mb-2 font-bold text-primary">Règles de remplacement personnalisées</h3>
  <CustomRulesManager
      currentRules={customReplacementRules}
      error={customRuleError}
      on:addrule={handleAddCustomRule}
      on:removerule={handleRemoveCustomRule}
  />

  <div class="flex gap-4 mt-2 mb-2">
      <button
          class="btn-primary mr-2"
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
          class="btn-secondary"
          type="button"
          on:click={resetAll}
          disabled={isLoading}
      >
          Réinitialiser
      </button>
  </div>

  <ResultView
      inputText={localInput}
      outputText={localOutput}
      auditLog={localAuditLog}
      showSplitView={showSplitView}
      showOriginal={showOriginal}
      copied={copied}
      onToggleSplitView={() => showSplitView = !showSplitView}
      onToggleShowOriginal={() => showOriginal = !showOriginal}
      onCopyOutput={copyOutput}
      onExportOutput={exportOutput}
      isLoading={isLoading}
      on:showLog={() => dispatch('showLog')}
  />

  {#if errorMessage}
      <div class="card-panel card-error mt-4">
          <strong>Erreur lors de l’anonymisation :</strong>
          <pre class="whitespace-pre-wrap text-xs">{errorMessage}</pre>
      </div>
  {/if}
</div>
