<!-- #anonyfiles/anonyfiles_gui/src/lib/components/LogView.svelte -->
<script lang="ts">
  import { auditLog } from '../stores/anonymizationStore';

  // Store auditLog, tableau d’objets { pattern, replacement, type, count }
  // Ici on suppose ces clés, adapte selon ta structure réelle

  $: totalOccurrences = $auditLog.reduce((sum, item) => sum + (item.count || 0), 0);
</script>

<div class="overflow-x-auto max-w-full p-4 bg-white dark:bg-zinc-900 rounded-lg shadow-lg">
  <h2 class="text-center text-xl font-semibold mb-4 text-primary">Journal des anonymisations</h2>
  <table class="w-full border-collapse text-sm">
    <thead class="bg-gray-100 dark:bg-gray-800">
      <tr>
        <th class="border border-gray-300 dark:border-gray-700 px-3 py-2 text-left">Motif</th>
        <th class="border border-gray-300 dark:border-gray-700 px-3 py-2 text-left">Remplacement</th>
        <th class="border border-gray-300 dark:border-gray-700 px-3 py-2 text-left">Type</th>
        <th class="border border-gray-300 dark:border-gray-700 px-3 py-2 text-right">Nb occur.</th>
      </tr>
    </thead>
    <tbody>
      {#each $auditLog as logItem (logItem.pattern + logItem.replacement)}
        <tr class="hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer select-text">
          <td class="border border-gray-300 dark:border-gray-700 px-3 py-1">{logItem.pattern}</td>
          <td class="border border-gray-300 dark:border-gray-700 px-3 py-1">{logItem.replacement}</td>
          <td class="border border-gray-300 dark:border-gray-700 px-3 py-1">{logItem.type}</td>
          <td class="border border-gray-300 dark:border-gray-700 px-3 py-1 text-right">{logItem.count}</td>
        </tr>
      {/each}
    </tbody>
    <tfoot>
      <tr class="bg-gray-100 dark:bg-gray-800 font-semibold">
        <td colspan="3" class="border border-gray-300 dark:border-gray-700 px-3 py-2 text-right">Total</td>
        <td class="border border-gray-300 dark:border-gray-700 px-3 py-2 text-right">{totalOccurrences}</td>
      </tr>
    </tfoot>
  </table>
</div>
