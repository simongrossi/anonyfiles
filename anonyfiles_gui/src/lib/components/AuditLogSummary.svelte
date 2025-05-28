<!-- #anonyfiles/anonyfiles_gui/src/lib/components/AuditLogSummary.svelte -->
<script lang="ts">
  import { auditLog } from '../stores/anonymizationStore';
</script>

<div class="flex justify-center items-center min-h-[60vh]">
  <div class="w-full max-w-3xl bg-white dark:bg-zinc-950 shadow-xl rounded-2xl p-8">
    <h2 class="text-2xl font-bold text-blue-800 mb-6 text-center">Journal des anonymisations</h2>
    <div class="overflow-x-auto">
      <table class="min-w-full table-auto border-collapse">
        <thead>
          <tr class="bg-blue-50 dark:bg-zinc-800">
            <th class="px-3 py-2 text-left font-semibold text-zinc-700 dark:text-zinc-200">Motif</th>
            <th class="px-3 py-2 text-left font-semibold text-zinc-700 dark:text-zinc-200">Remplacement</th>
            <th class="px-3 py-2 text-left font-semibold text-zinc-700 dark:text-zinc-200">Type</th>
            <th class="px-3 py-2 text-left font-semibold text-zinc-700 dark:text-zinc-200">Nb occur.</th>
          </tr>
        </thead>
        <tbody>
          {#if $auditLog.length === 0}
            <tr>
              <td class="px-3 py-3 text-zinc-500 text-center" colspan="4">
                Aucune anonymisation n’a encore été réalisée.
              </td>
            </tr>
          {:else}
            {#each $auditLog as entry}
              <tr class="border-b border-zinc-200 hover:bg-blue-50/50 dark:hover:bg-zinc-900 transition">
                <td class="px-3 py-2 font-mono text-[0.97em]">{entry.pattern}</td>
                <td class="px-3 py-2 font-mono text-[0.97em]">{entry.replacement}</td>
                <td class="px-3 py-2 text-xs">{entry.type}</td>
                <td class="px-3 py-2 text-center">{entry.count ?? 1}</td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </div>
  </div>
</div>
