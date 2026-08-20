<script lang="ts">
  import {
    inputText,
    outputText,
    mappingCSV,
    auditLog,
    privacyWarnings,
    outputLineCount,
    outputCharCount,
    outputFileName,
    outputIsBinary,
  } from '../stores/anonymizationStore';
  import { currentJobId } from '$lib/stores/jobStore';
  import { fileName } from '../utils/useFileHandler';
  import { apiFetch, apiUrl } from '../utils/api';
  import { saveFile, saveTextFile, suffixedFileName } from '../utils/download';
  import { copyTextToClipboard } from '../utils/clipboard';
  import {
    FileText,
    FileInput,
    GitCompare,
    Table,
    Copy,
    Download,
    FileDown,
    CircleCheck,
    AlertTriangle,
  } from 'lucide-svelte';

  type ViewMode = 'anonymized' | 'original' | 'split' | 'mapping';
  interface ResultTab {
    id: ViewMode;
    label: string;
    icon: typeof FileText;
  }

  let viewMode: ViewMode = $state('anonymized');

  const hasText = $derived($outputText.trim().length > 0);
  // Une sortie .docx / .pdf / .xlsx n'a pas d'aperçu texte : sans ce cas, le
  // panneau de résultat restait entièrement masqué et l'anonymisation semblait
  // n'avoir rien produit.
  const hasBinaryOutput = $derived($outputIsBinary && !!$currentJobId);
  const hasOutput = $derived(hasText || hasBinaryOutput);
  const hasPrivacyWarnings = $derived($privacyWarnings.length > 0);

  const outputSuggestedName = $derived(
    suffixedFileName($fileName, '_anonymise', $outputFileName || 'anonymized.txt')
  );

  const totalReplacements = $derived(
    $auditLog.reduce((sum, item) => sum + (item.count || 0), 0)
  );

  // Sans aperçu texte (sortie .docx / .pdf / .xlsx), les onglets qui affichent
  // le résultat anonymisé n'ont rien à montrer.
  const tabs: ResultTab[] = $derived([
    ...(hasText
      ? [
          { id: 'anonymized' as const, label: 'Anonymisé', icon: FileText },
          { id: 'original' as const, label: 'Original', icon: FileInput },
          { id: 'split' as const, label: 'Comparaison', icon: GitCompare },
        ]
      : [{ id: 'original' as const, label: 'Original', icon: FileInput }]),
    { id: 'mapping' as const, label: 'Mapping', icon: Table },
  ]);

  $effect(() => {
    if (!tabs.some((tab) => tab.id === viewMode)) {
      viewMode = tabs[0].id;
    }
  });

  let exportError = $state('');
  let isDownloading = $state(false);

  async function exportOutput() {
    exportError = '';
    if (await saveTextFile($outputText, outputSuggestedName) === 'error') {
      exportError = "Impossible d'enregistrer le fichier anonymisé.";
    }
  }

  async function exportMapping() {
    if (!$mappingCSV.trim()) return;
    exportError = '';
    if (await saveTextFile($mappingCSV, 'mapping.csv', 'text/csv;charset=utf-8') === 'error') {
      exportError = "Impossible d'enregistrer le mapping.";
    }
  }

  /**
   * Récupère le fichier de sortie tel quel auprès de l'API. Indispensable pour
   * les formats binaires (.docx, .pdf, .xlsx) que le front ne reçoit jamais
   * sous forme de texte.
   */
  async function downloadOutputFile() {
    const jobId = $currentJobId;
    if (!jobId) return;
    exportError = '';
    isDownloading = true;
    try {
      const response = await apiFetch(await apiUrl(`files/${jobId}/output?as_attachment=true`));
      if (!response.ok) {
        exportError = `Téléchargement impossible (HTTP ${response.status}).`;
        return;
      }
      const mime = response.headers.get('content-type') || 'application/octet-stream';
      const bytes = await response.arrayBuffer();
      if (await saveFile(bytes, outputSuggestedName, mime) === 'error') {
        exportError = "Impossible d'enregistrer le fichier anonymisé.";
      }
    } catch (err: any) {
      exportError = err?.message || 'Téléchargement impossible.';
    } finally {
      isDownloading = false;
    }
  }

  let copied = $state(false);
  async function copyOutput() {
    if (await copyTextToClipboard($outputText)) {
      copied = true;
      setTimeout(() => (copied = false), 1500);
    }
  }
</script>

{#if hasOutput}
  <section class="ui-section mt-2">
    <header class="ui-section-header justify-between flex-wrap gap-2">
      <div class="flex items-center gap-2">
        <CircleCheck size={16} class="text-emerald-500" />
        <span class="ui-section-title">Résultat de l'anonymisation</span>
        <span class="ui-badge-brand">
          {totalReplacements} substitution{totalReplacements > 1 ? 's' : ''}
        </span>
      </div>
      <div class="flex items-center gap-1">
        {#if hasText}
          <button type="button" class="ui-btn-ghost text-xs px-2 py-1" on:click={copyOutput}>
            <Copy size={14} />
            {copied ? 'Copié !' : 'Copier'}
          </button>
          <button type="button" class="ui-btn-ghost text-xs px-2 py-1" on:click={exportOutput}>
            <Download size={14} />
            Exporter
          </button>
        {/if}
        {#if $currentJobId}
          <button
            type="button"
            class="ui-btn-ghost text-xs px-2 py-1"
            on:click={downloadOutputFile}
            disabled={isDownloading}
          >
            <FileDown size={14} />
            {isDownloading ? 'Téléchargement…' : 'Télécharger le fichier'}
          </button>
        {/if}
      </div>
    </header>

    <div class="ui-section-body space-y-4">
      {#if exportError}
        <div class="rounded-xl border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/30 text-red-800 dark:text-red-200 px-4 py-3 text-sm">
          {exportError}
        </div>
      {/if}

      {#if hasBinaryOutput}
        <div
          class="rounded-xl border border-brand-500/40 bg-brand-50 dark:bg-brand-900/25 text-brand-700 dark:text-brand-100 px-4 py-3"
          role="status"
        >
          <div class="flex items-start gap-2">
            <FileDown size={18} class="shrink-0 mt-0.5" />
            <div class="min-w-0">
              <strong class="font-semibold">Fichier anonymisé prêt</strong>
              <p class="mt-1 text-sm">
                Ce format ({$outputFileName ? $outputFileName.split('.').pop() : 'binaire'}) ne
                peut pas être affiché en aperçu texte. Utilise
                <span class="font-medium">« Télécharger le fichier »</span> pour l'enregistrer.
              </p>
            </div>
          </div>
        </div>
      {/if}

      {#if hasPrivacyWarnings}
        <div
          class="rounded-xl border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/25 text-amber-900 dark:text-amber-100 px-4 py-3"
          role="status"
        >
          <div class="flex items-start gap-2">
            <AlertTriangle size={18} class="shrink-0 mt-0.5" />
            <div class="min-w-0">
              <strong class="font-semibold">Éléments suspects restants</strong>
              <div class="mt-2 space-y-2 text-sm">
                {#each $privacyWarnings as warning}
                  <div>
                    <span class="font-medium">{warning.message}</span>
                    {#if warning.examples?.length}
                      <span class="block mt-1 text-xs text-amber-800/80 dark:text-amber-100/80 wrap-break-word">
                        Exemples : {warning.examples.join(', ')}
                      </span>
                    {/if}
                  </div>
                {/each}
              </div>
            </div>
          </div>
        </div>
      {/if}

      <!-- Segmented control -->
      <div class="grid grid-cols-2 sm:inline-flex p-1 rounded-xl bg-zinc-100 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-700 max-w-full gap-1">
        {#each tabs as tab}
          {@const Icon = tab.icon}
          {@const active = viewMode === tab.id}
          <button
            type="button"
            class="min-w-0 inline-flex items-center justify-center gap-1.5 px-2 sm:px-3 py-1.5 rounded-lg text-xs font-medium transition
                   {active
                     ? 'bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 shadow-sm'
                     : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-zinc-200'}"
            on:click={() => (viewMode = tab.id)}
            aria-pressed={active}
          >
            <Icon size={14} class="shrink-0" />
            <span class="truncate">{tab.label}</span>
          </button>
        {/each}
      </div>

      {#if viewMode === 'anonymized'}
        <div>
          <div class="flex items-center justify-between mb-1">
            <label class="ui-field-label mb-0!" for="anonymized-text">Texte anonymisé</label>
            <span class="text-[11px] text-zinc-400 dark:text-zinc-500 tabular-nums">
              {$outputLineCount} lignes · {$outputCharCount} car.
            </span>
          </div>
          <pre
            id="anonymized-text"
            class="rounded-xl border border-emerald-200 dark:border-emerald-800 bg-emerald-50/60 dark:bg-emerald-900/20
                   text-emerald-900 dark:text-emerald-100 font-mono text-sm px-4 py-3 max-h-72 overflow-auto
                   whitespace-pre-wrap wrap-break-word"
          >{$outputText}</pre>
        </div>
      {/if}

      {#if viewMode === 'original'}
        <div>
          <label class="ui-field-label" for="original-text">Texte original</label>
          <pre
            id="original-text"
            class="rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-900
                   text-zinc-800 dark:text-zinc-100 font-mono text-sm px-4 py-3 max-h-72 overflow-auto
                   whitespace-pre-wrap wrap-break-word"
          >{$inputText}</pre>
        </div>
      {/if}

      {#if viewMode === 'split'}
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <span class="ui-field-label">Original</span>
            <pre
              class="rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-900
                     text-zinc-800 dark:text-zinc-100 font-mono text-sm px-4 py-3 max-h-72 overflow-auto
                     whitespace-pre-wrap wrap-break-word"
            >{$inputText}</pre>
          </div>
          <div>
            <div class="flex items-center justify-between">
              <span class="ui-field-label">Anonymisé</span>
              <span class="text-[11px] text-zinc-400 dark:text-zinc-500 tabular-nums">
                {$outputLineCount} · {$outputCharCount}
              </span>
            </div>
            <pre
              class="rounded-xl border border-emerald-200 dark:border-emerald-800 bg-emerald-50/60 dark:bg-emerald-900/20
                     text-emerald-900 dark:text-emerald-100 font-mono text-sm px-4 py-3 max-h-72 overflow-auto
                     whitespace-pre-wrap wrap-break-word"
            >{$outputText}</pre>
          </div>
        </div>
      {/if}

      {#if viewMode === 'mapping'}
        <div>
          <div class="flex items-center justify-between mb-1">
            <label class="ui-field-label mb-0!" for="mapping-text">Fichier de mapping généré</label>
            {#if $mappingCSV && $mappingCSV.trim()}
              <button type="button" class="ui-btn-ghost text-xs px-2 py-1" on:click={exportMapping}>
                <Download size={14} />
                Exporter CSV
              </button>
            {/if}
          </div>
          <pre
            id="mapping-text"
            class="rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-900
                   text-zinc-700 dark:text-zinc-200 font-mono text-xs px-4 py-3 max-h-72 overflow-auto
                   whitespace-pre-wrap wrap-break-word"
          >{$mappingCSV || 'Aucun mapping généré ou disponible.'}</pre>
        </div>
      {/if}
    </div>
  </section>
{/if}
