<script lang="ts">
  import {
    inputText,
    outputText,
    mappingCSV,
    auditLog,
    outputLineCount,
    outputCharCount,
  } from '../stores/anonymizationStore';
  import {
    FileText,
    FileInput,
    GitCompare,
    Table,
    Copy,
    Download,
    CircleCheck,
  } from 'lucide-svelte';

  let viewMode: 'anonymized' | 'original' | 'split' | 'mapping' = 'anonymized';

  $: hasOutput = $outputText && $outputText.trim().length > 0;

  $: totalReplacements = $auditLog.reduce((sum, item) => sum + (item.count || 0), 0);

  const tabs: Array<{ id: typeof viewMode; label: string; icon: typeof FileText }> = [
    { id: 'anonymized', label: 'Anonymisé', icon: FileText },
    { id: 'original', label: 'Original', icon: FileInput },
    { id: 'split', label: 'Comparaison', icon: GitCompare },
    { id: 'mapping', label: 'Mapping', icon: Table },
  ];

  function exportOutput() {
    const blob = new Blob([$outputText], { type: 'text/plain;charset=utf-8' });
    const link = document.createElement('a');
    link.download = 'anonymized.txt';
    link.href = URL.createObjectURL(blob);
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      URL.revokeObjectURL(link.href);
      document.body.removeChild(link);
    }, 200);
  }

  function exportMapping() {
    if (!$mappingCSV.trim()) return;
    const blob = new Blob([$mappingCSV], { type: 'text/csv;charset=utf-8' });
    const link = document.createElement('a');
    link.download = 'mapping.csv';
    link.href = URL.createObjectURL(blob);
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      URL.revokeObjectURL(link.href);
      document.body.removeChild(link);
    }, 200);
  }

  let copied = false;
  async function copyOutput() {
    try {
      await navigator.clipboard.writeText($outputText);
      copied = true;
      setTimeout(() => (copied = false), 1500);
    } catch {}
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
        <button type="button" class="ui-btn-ghost text-xs px-2 py-1" on:click={copyOutput}>
          <Copy size={14} />
          {copied ? 'Copié !' : 'Copier'}
        </button>
        <button type="button" class="ui-btn-ghost text-xs px-2 py-1" on:click={exportOutput}>
          <Download size={14} />
          Exporter
        </button>
      </div>
    </header>

    <div class="ui-section-body space-y-4">
      <!-- Segmented control -->
      <div class="inline-flex p-1 rounded-xl bg-zinc-100 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-700">
        {#each tabs as tab}
          {@const Icon = tab.icon}
          {@const active = viewMode === tab.id}
          <button
            type="button"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition
                   {active
                     ? 'bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 shadow-sm'
                     : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-zinc-200'}"
            on:click={() => (viewMode = tab.id)}
            aria-pressed={active}
          >
            <Icon size={14} />
            {tab.label}
          </button>
        {/each}
      </div>

      {#if viewMode === 'anonymized'}
        <div>
          <div class="flex items-center justify-between mb-1">
            <label class="ui-field-label !mb-0" for="anonymized-text">Texte anonymisé</label>
            <span class="text-[11px] text-zinc-400 dark:text-zinc-500 tabular-nums">
              {$outputLineCount} lignes · {$outputCharCount} car.
            </span>
          </div>
          <pre
            id="anonymized-text"
            class="rounded-xl border border-emerald-200 dark:border-emerald-800 bg-emerald-50/60 dark:bg-emerald-900/20
                   text-emerald-900 dark:text-emerald-100 font-mono text-sm px-4 py-3 max-h-72 overflow-auto
                   whitespace-pre-wrap break-words"
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
                   whitespace-pre-wrap break-words"
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
                     whitespace-pre-wrap break-words"
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
                     whitespace-pre-wrap break-words"
            >{$outputText}</pre>
          </div>
        </div>
      {/if}

      {#if viewMode === 'mapping'}
        <div>
          <div class="flex items-center justify-between mb-1">
            <label class="ui-field-label !mb-0" for="mapping-text">Fichier de mapping généré</label>
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
                   whitespace-pre-wrap break-words"
          >{$mappingCSV || 'Aucun mapping généré ou disponible.'}</pre>
        </div>
      {/if}
    </div>
  </section>
{/if}
