<!-- #anonyfiles/anonyfiles_gui/src/lib/components/AuditLogTable.svelte -->
<script lang="ts">
  export let logs: any[] = [];
</script>

<table class="min-w-full divide-y divide-zinc-200 bg-zinc-50 rounded-lg overflow-hidden">
  <thead>
    <tr class="bg-zinc-100">
      <th class="px-3 py-2 text-left text-xs font-medium text-zinc-500 uppercase">Motif</th>
      <th class="px-3 py-2 text-left text-xs font-medium text-zinc-500 uppercase">Remplacement</th>
      <th class="px-3 py-2 text-left text-xs font-medium text-zinc-500 uppercase">Type</th>
      <th class="px-3 py-2 text-left text-xs font-medium text-zinc-500 uppercase">Nb occur.</th>
    </tr>
  </thead>
  <tbody class="divide-y divide-zinc-200">
    {#each logs as entry, idx}
      <tr>
        <td class="px-3 py-1 whitespace-pre-wrap font-mono text-xs">{entry.pattern}</td>
        <td class="px-3 py-1 whitespace-pre-wrap font-mono text-xs">{entry.replacement}</td>
        <td class="px-3 py-1 whitespace-pre-wrap font-mono text-xs">{entry.type}</td>
        <td class="px-3 py-1 whitespace-pre-wrap font-mono text-xs">{entry.count}</td>
      </tr>
    {/each}
  </tbody>
</table>
