<script lang="ts">
  import FileDropZone from './FileDropZone.svelte';
  import { onDestroy } from 'svelte';
  import {
    Unlock,
    FileText,
    FileSpreadsheet,
    Loader2,
    RotateCcw,
    AlertTriangle,
    Download,
    Copy,
    ListChecks,
  } from 'lucide-svelte';
  import { apiUrl, pollJob, debug } from '$lib/utils/api';

  let inputFile: File | null = null;
  let mappingFile: File | null = null;
  let outputText: string = '';
  let isLoading: boolean = false;
  let errorMessage: string = '';
  let report: string[] = [];
  let permissive: boolean = false;
  let abortController: AbortController | null = null;

  function resetAll() {
    inputFile = null;
    mappingFile = null;
    outputText = '';
    errorMessage = '';
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
    errorMessage = '';
    if (zoneIdFromEvent === 'input-file-zone') {
      inputFile = file;
    } else if (zoneIdFromEvent === 'mapping-file-zone') {
      if (file.type === 'text/csv' || file.name.toLowerCase().endsWith('.csv')) {
        mappingFile = file;
      } else {
        mappingFile = null;
        errorMessage = 'Le fichier de mapping doit être un fichier .csv';
      }
    }
  }

  function handleClear(zoneId: string) {
    if (zoneId === 'input-file-zone') inputFile = null;
    if (zoneId === 'mapping-file-zone') mappingFile = null;
  }

  async function deanonymize() {
    if (!inputFile || !mappingFile) {
      errorMessage = 'Merci de sélectionner un fichier à désanonymiser ET un fichier de mapping CSV.';
      isLoading = false;
      return;
    }

    errorMessage = '';
    outputText = '';
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
      debug('DeAnonymizer: Appel API:', deanonymizeEndpoint);

      const response = await fetch(deanonymizeEndpoint, { method: 'POST', body: formData, signal });
      const data = await response.json();

      if (!response.ok) throw new Error(data?.detail || data?.error || `Erreur HTTP ${response.status}`);

      const jobId = data.job_id;
      if (!jobId) throw new Error(data?.error || 'job_id absent de la réponse API.');

      const statusData = await pollJob<{
        status: string;
        deanonymized_text?: string;
        audit_log?: string[];
        error?: string;
      }>(await apiUrl(`deanonymize_status/${jobId}`), { signal });

      outputText = statusData.deanonymized_text || '';
      report = statusData.audit_log || [];
      isLoading = false;
    } catch (e: any) {
      if (e?.name !== 'AbortError') {
        errorMessage = e.message || 'Erreur lancement désanonymisation.';
      }
      isLoading = false;
    }
  }

  async function copyOutput() {
    try {
      await navigator.clipboard.writeText(outputText);
    } catch {}
  }

  function exportOutput() {
    const blob = new Blob([outputText], { type: 'text/plain;charset=utf-8' });
    const link = document.createElement('a');
    link.download = 'deanonymized.txt';
    link.href = URL.createObjectURL(blob);
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      URL.revokeObjectURL(link.href);
      document.body.removeChild(link);
    }, 200);
  }

  onDestroy(() => {
    if (abortController) abortController.abort();
  });
</script>

<div class="w-full max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 pb-10">
  <div class="mb-5 flex items-center gap-3">
    <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 dark:bg-brand-900/30 text-brand-600 dark:text-brand-100">
      <Unlock size={20} />
    </div>
    <div>
      <h1 class="text-lg font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
        Désanonymiser un fichier
      </h1>
      <p class="text-xs text-zinc-500 dark:text-zinc-400">
        Restaurer les données d'origine à partir d'un fichier anonymisé et de son mapping CSV.
      </p>
    </div>
  </div>

  <!-- Section 1 — Fichiers -->
  <section class="ui-section mb-5">
    <header class="ui-section-header">
      <FileText size={16} class="text-zinc-400 dark:text-zinc-500" />
      <span class="ui-section-title">Fichiers</span>
      <span class="ui-section-subtitle">&middot; source + mapping CSV</span>
    </header>
    <div class="ui-section-body grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <span class="ui-field-label flex items-center gap-1.5">
          <FileText size={12} />
          Fichier anonymisé à restaurer
        </span>
        <FileDropZone
          id="deanonymize-input-file"
          dropZoneId="input-file-zone"
          fileName={inputFile ? inputFile.name : ''}
          accept=".txt,.csv,.xlsx,.docx,.pdf,.json"
          on:file={handleFileDropped}
          on:clear={() => handleClear('input-file-zone')}
        />
      </div>
      <div>
        <span class="ui-field-label flex items-center gap-1.5">
          <FileSpreadsheet size={12} />
          Fichier de mapping (CSV)
        </span>
        <FileDropZone
          id="deanonymize-mapping-file"
          dropZoneId="mapping-file-zone"
          fileName={mappingFile ? mappingFile.name : ''}
          accept=".csv"
          on:file={handleFileDropped}
          on:clear={() => handleClear('mapping-file-zone')}
        />
      </div>
    </div>
  </section>

  <!-- Section 2 — Options -->
  <section class="ui-section mb-5">
    <header class="ui-section-header">
      <ListChecks size={16} class="text-zinc-400 dark:text-zinc-500" />
      <span class="ui-section-title">Options</span>
    </header>
    <div class="ui-section-body">
      <label class="inline-flex items-start gap-3 cursor-pointer group">
        <span class="relative shrink-0 mt-0.5">
          <input
            type="checkbox"
            bind:checked={permissive}
            class="peer sr-only"
            disabled={isLoading}
          />
          <span
            class="block h-5 w-9 rounded-full bg-zinc-300 dark:bg-zinc-600 peer-checked:bg-brand-600
                   peer-focus-visible:ring-2 peer-focus-visible:ring-brand-500/40 transition-colors"
          ></span>
          <span
            class="absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white shadow-sm transition-transform
                   peer-checked:translate-x-4"
          ></span>
        </span>
        <span>
          <span class="block text-sm font-medium text-zinc-800 dark:text-zinc-100">Mode permissif</span>
          <span class="block text-xs text-zinc-500 dark:text-zinc-400">
            Ignore les entrées de mapping manquantes au lieu d'interrompre le traitement.
          </span>
        </span>
      </label>
    </div>
  </section>

  <!-- Actions -->
  <div class="sticky bottom-4 z-30 mt-6">
    <div class="flex flex-col sm:flex-row gap-2 justify-end rounded-2xl bg-white/80 dark:bg-zinc-800/80 backdrop-blur border border-zinc-200 dark:border-zinc-700 shadow-card px-4 py-3">
      <button
        type="button"
        class="ui-btn-secondary"
        on:click={resetAll}
        disabled={isLoading}
      >
        <RotateCcw size={16} />
        Réinitialiser
      </button>
      <button
        type="button"
        class="ui-btn-primary"
        on:click={deanonymize}
        disabled={isLoading || !inputFile || !mappingFile}
        aria-busy={isLoading}
      >
        {#if isLoading}
          <Loader2 size={16} class="animate-spin" />
          Traitement…
        {:else}
          <Unlock size={16} />
          Désanonymiser
        {/if}
      </button>
    </div>
  </div>

  {#if errorMessage}
    <div
      class="mt-4 rounded-2xl border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/30 text-red-800 dark:text-red-200 px-4 py-3"
      role="alert"
    >
      <div class="flex items-start gap-2">
        <AlertTriangle size={18} class="shrink-0 mt-0.5" />
        <div>
          <strong class="font-semibold">Erreur</strong>
          <pre class="whitespace-pre-wrap text-xs font-mono mt-1">{typeof errorMessage === 'object' ? JSON.stringify(errorMessage, null, 2) : errorMessage}</pre>
        </div>
      </div>
    </div>
  {/if}

  {#if outputText}
    <section class="ui-section mt-6">
      <header class="ui-section-header justify-between">
        <div class="flex items-center gap-2">
          <FileText size={16} class="text-zinc-400 dark:text-zinc-500" />
          <span class="ui-section-title">Fichier désanonymisé</span>
        </div>
        <div class="flex items-center gap-1">
          <button type="button" class="ui-btn-ghost text-xs px-2 py-1" on:click={copyOutput}>
            <Copy size={14} />
            Copier
          </button>
          <button type="button" class="ui-btn-ghost text-xs px-2 py-1" on:click={exportOutput}>
            <Download size={14} />
            Exporter
          </button>
        </div>
      </header>
      <div class="ui-section-body">
        <textarea
          class="ui-textarea font-mono text-sm min-h-[12rem]"
          readonly
          value={outputText}
          rows="10"
        ></textarea>
      </div>
    </section>
  {/if}

  {#if report && report.length > 0}
    <section class="ui-section mt-6">
      <header class="ui-section-header">
        <ListChecks size={16} class="text-zinc-400 dark:text-zinc-500" />
        <span class="ui-section-title">Journal / Avertissements</span>
      </header>
      <div class="ui-section-body">
        <ul class="space-y-1.5 text-sm text-zinc-700 dark:text-zinc-200">
          {#each report as message}
            <li class="flex items-start gap-2">
              <span class="mt-1.5 h-1 w-1 rounded-full bg-zinc-400 shrink-0"></span>
              <span>{typeof message === 'object' ? JSON.stringify(message) : message}</span>
            </li>
          {/each}
        </ul>
      </div>
    </section>
  {/if}
</div>
