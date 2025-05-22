<script lang="ts">
    import CsvPreview from './CsvPreview.svelte';
    import XlsxPreview from './XlsxPreview.svelte';
    import CustomRulesManager from './CustomRulesManager.svelte';
    import { onMount } from 'svelte';
    import { createEventDispatcher } from 'svelte';
    const dispatch = createEventDispatcher();

    // Props reçues du parent pour initialisation
    export let inputText: string = "";
    export let outputText: string = "";
    export let auditLog: any[] = [];

    // State local pour l’édition active
    let localInput = "";
    let localOutput = "";
    let localAuditLog = [];

    // Calcul du total de remplacements (compteur)
    $: totalReplacements = localAuditLog.reduce((sum, log) => sum + (log.count || 0), 0);

    // Initialisation uniquement au montage
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

    // Custom rules state
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

    // Calcul du bouton Anonymiser
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

    // Règles custom
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

    // Polling
    let pollingInterval: any = null;

    // Appel backend (web, asynchrone)
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

        try {
            const API_URL = import.meta.env.VITE_ANONYFILES_API_URL || 'http://localhost:8000';
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
            // customReplacementRules inclus dans configForBackend

            // 1. Création du job
            const response = await fetch(`${API_URL}/anonymize/`, {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Erreur lors de la création du job.');
            }
            const jobId = data.job_id;
            if (!jobId) throw new Error("job_id absent de la réponse API");

            // 2. Polling
            pollingInterval = setInterval(async () => {
                const statusResp = await fetch(`${API_URL}/anonymize_status/${jobId}`);
                const statusData = await statusResp.json();
                if (statusData.status === "finished") {
                    clearInterval(pollingInterval);
                    localOutput = statusData.anonymized_text;
                    localAuditLog = statusData.audit_log || [];
                    isLoading = false;
                    // On prévient le parent qu’il faut stocker le résultat
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
                // pending : ne rien faire
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
        dispatch('resetRequested'); // Préviens le parent qu'il faut reset l’état global
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

<div
    role="region"
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
        class="px-6 py-2 font-semibold text-white rounded-xl bg-blue-700 hover:bg-blue-800 active:bg-blue-900 shadow-sm transition-all disabled:bg-zinc-400 disabled:cursor-wait mr-2"
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

{#if localOutput}
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
        {#if showSplitView}
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="flex flex-col">
                    <span class="mb-1 font-semibold text-zinc-600 dark:text-zinc-300">Texte original</span>
                    <textarea
                        class="bg-white text-zinc-900 p-3 rounded-xl resize-y min-h-[60px] border border-zinc-300 font-mono w-full dark:bg-gray-800 dark:text-zinc-100 dark:border-gray-600"
                        readonly
                        value={localInput}
                        rows="6"
                    />
                </div>
                <div class="flex flex-col">
                    <span class="mb-1 font-semibold text-green-800 dark:text-green-300">Texte anonymisé</span>
                    <textarea
                        class="bg-green-50 text-green-900 p-3 rounded-xl resize-y min-h-[60px] border border-green-200 font-mono w-full dark:bg-green-800 dark:text-green-100 dark:border-green-700"
                        readonly
                        bind:value={localOutput}
                        rows="6"
                    />
                    <div class="flex gap-2 justify-end mt-2">
                        <button
                            class="flex items-center gap-1 px-4 py-1.5 rounded-md bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow transition disabled:opacity-60"
                            type="button"
                            on:click={copyOutput}
                            disabled={copied}
                        >
                            {#if copied}
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                                </svg>
                                Copié !
                            {:else}
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <rect x="9" y="9" width="13" height="13" rx="2" stroke="currentColor" stroke-width="2"/>
                                    <rect x="3" y="3" width="13" height="13" rx="2" stroke="currentColor" stroke-width="2"/>
                                </svg>
                                Copier
                            {/if}
                        </button>
                        <button
                            class="flex items-center gap-1 px-4 py-1.5 rounded-md bg-green-700 hover:bg-green-800 text-white font-semibold shadow transition"
                            type="button"
                            on:click={exportOutput}
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v16h16V4H4zm4 8h8m-4-4v8"/>
                            </svg>
                            Exporter
                        </button>
                    </div>
                </div>
            </div>
        {:else}
            <div class="flex flex-col gap-2">
                <span class="mb-1 font-semibold dark:text-zinc-200">{showOriginal ? "Texte original" : "Texte anonymisé"}</span>
                <textarea
                    class={showOriginal
                        ? "bg-white text-zinc-900 p-3 rounded-xl resize-y min-h-[60px] border border-zinc-300 font-mono w-full dark:bg-gray-800 dark:text-zinc-100 dark:border-gray-600"
                        : "bg-green-50 text-green-900 p-3 rounded-xl resize-y min-h-[60px] border border-green-200 font-mono w-full dark:bg-green-800 dark:text-green-100 dark:border-green-700"}
                    readonly
                    value={showOriginal ? localInput : localOutput}
                    rows="6"
                />
                {#if !showOriginal}
                    <div class="flex gap-2 justify-end mt-2">
                        <button
                            class="flex items-center gap-1 px-4 py-1.5 rounded-md bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow transition disabled:opacity-60"
                            type="button"
                            on:click={copyOutput}
                            disabled={copied}
                        >
                            {#if copied}
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                                </svg>
                                Copié !
                            {:else}
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <rect x="9" y="9" width="13" height="13" rx="2" stroke="currentColor" stroke-width="2"/>
                                    <rect x="3" y="3" width="13" height="13" rx="2" stroke="currentColor" stroke-width="2"/>
                                </svg>
                                Copier
                            {/if}
                        </button>
                        <button
                            class="flex items-center gap-1 px-4 py-1.5 rounded-md bg-green-700 hover:bg-green-800 text-white font-semibold shadow transition"
                            type="button"
                            on:click={exportOutput}
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v16h16V4H4zm4 8h8m-4-4v8"/>
                            </svg>
                            Exporter
                        </button>
                    </div>
                {/if}
            </div>
        {/if}
    </div>
{/if}

{#if errorMessage}
    <div class="border border-red-200 bg-red-50 text-red-800 rounded-xl p-3 mt-4 dark:border-red-600 dark:bg-red-900 dark:text-red-300">
        <strong>Erreur lors de l’anonymisation :</strong>
        <pre class="whitespace-pre-wrap text-xs">{errorMessage}</pre>
    </div>
{/if}

{#if localAuditLog.length}
    <div class="mt-6 p-4 rounded-xl bg-blue-50 border border-blue-200 dark:bg-blue-900 dark:border-blue-800">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-2">
            <div class="font-semibold text-blue-800 dark:text-blue-200">Résumé des règles appliquées :</div>
            <div class="text-xs font-semibold text-blue-900 dark:text-blue-100 mt-1 sm:mt-0">
                Total anonymisations&nbsp;: 
                <span class="font-bold">{totalReplacements}</span>
            </div>
        </div>
        <ul class="space-y-1 text-blue-900 dark:text-blue-100 text-sm">
            {#each localAuditLog as log}
                <li>
                    {log.pattern} → {log.replacement}
                    <span class="ml-2 text-xs rounded bg-gray-200 dark:bg-gray-700 px-1">{log.type}</span>
                    <span class="ml-2 text-xs text-gray-500">{log.count} remplacement{log.count > 1 ? 's' : ''}</span>
                </li>
            {/each}
        </ul>
    </div>
{/if}
