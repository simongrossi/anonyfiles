<!-- #anonyfiles/anonyfiles_gui/src/lib/components/LogView.svelte -->
<script lang="ts">
  import { auditLog } from '../stores/anonymizationStore';
  import { ScrollText, Hash, Tag } from 'lucide-svelte';

  $: totalOccurrences = $auditLog.reduce((sum, item) => sum + (item.count || 0), 0);
  $: distinctPatterns = $auditLog.length;
  $: distinctTypes = new Set($auditLog.map((i) => i.type || 'n/a')).size;
</script>

<div class="w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pb-10">
  <div class="mb-5 flex items-center gap-3">
    <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 dark:bg-brand-900/30 text-brand-600 dark:text-brand-100">
      <ScrollText size={20} />
    </div>
    <div>
      <h1 class="text-lg font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
        Journal des anonymisations
      </h1>
      <p class="text-xs text-zinc-500 dark:text-zinc-400">
        Synthèse des substitutions effectuées lors du dernier run.
      </p>
    </div>
  </div>

  <!-- Stats -->
  <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
    <div class="ui-section px-5 py-4 flex items-center gap-3">
      <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 dark:bg-brand-900/30 text-brand-600 dark:text-brand-100">
        <Hash size={18} />
      </div>
      <div>
        <div class="text-xl font-semibold text-zinc-900 dark:text-zinc-100 tabular-nums">
          {totalOccurrences}
        </div>
        <div class="text-xs text-zinc-500 dark:text-zinc-400">Occurrences totales</div>
      </div>
    </div>
    <div class="ui-section px-5 py-4 flex items-center gap-3">
      <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-zinc-100 dark:bg-zinc-700 text-zinc-600 dark:text-zinc-200">
        <Tag size={18} />
      </div>
      <div>
        <div class="text-xl font-semibold text-zinc-900 dark:text-zinc-100 tabular-nums">
          {distinctPatterns}
        </div>
        <div class="text-xs text-zinc-500 dark:text-zinc-400">Motifs distincts</div>
      </div>
    </div>
    <div class="ui-section px-5 py-4 flex items-center gap-3">
      <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-zinc-100 dark:bg-zinc-700 text-zinc-600 dark:text-zinc-200">
        <Tag size={18} />
      </div>
      <div>
        <div class="text-xl font-semibold text-zinc-900 dark:text-zinc-100 tabular-nums">
          {distinctTypes}
        </div>
        <div class="text-xs text-zinc-500 dark:text-zinc-400">Types d'entités</div>
      </div>
    </div>
  </div>

  <section class="ui-section">
    <header class="ui-section-header">
      <span class="ui-section-title">Détail</span>
    </header>
    {#if $auditLog.length === 0}
      <div class="ui-section-body text-sm text-zinc-500 dark:text-zinc-400 italic">
        Aucune entrée pour l'instant. Lance une anonymisation pour peupler le journal.
      </div>
    {:else}
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="text-[11px] uppercase tracking-wider text-zinc-500 dark:text-zinc-400 bg-zinc-50 dark:bg-zinc-900/60 border-b border-zinc-200 dark:border-zinc-700">
              <th class="px-5 py-2 text-left font-semibold">Motif</th>
              <th class="px-5 py-2 text-left font-semibold">Remplacement</th>
              <th class="px-5 py-2 text-left font-semibold">Type</th>
              <th class="px-5 py-2 text-right font-semibold">Nb occ.</th>
            </tr>
          </thead>
          <tbody>
            {#each $auditLog as logItem (logItem.pattern + logItem.replacement)}
              <tr
                class="border-b border-zinc-100 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-900/60 transition-colors"
              >
                <td class="px-5 py-2 font-mono text-xs text-zinc-800 dark:text-zinc-100 align-middle">
                  {logItem.pattern}
                </td>
                <td class="px-5 py-2 font-mono text-xs text-zinc-800 dark:text-zinc-100 align-middle">
                  {logItem.replacement}
                </td>
                <td class="px-5 py-2 align-middle">
                  <span class="ui-badge">{logItem.type || '—'}</span>
                </td>
                <td class="px-5 py-2 text-right tabular-nums text-zinc-700 dark:text-zinc-200 align-middle">
                  {logItem.count}
                </td>
              </tr>
            {/each}
          </tbody>
          <tfoot>
            <tr class="bg-zinc-50 dark:bg-zinc-900/60 font-semibold">
              <td colspan="3" class="px-5 py-2 text-right text-zinc-600 dark:text-zinc-300 text-xs uppercase tracking-wider">
                Total
              </td>
              <td class="px-5 py-2 text-right tabular-nums text-zinc-900 dark:text-zinc-100">
                {totalOccurrences}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    {/if}
  </section>
</div>
