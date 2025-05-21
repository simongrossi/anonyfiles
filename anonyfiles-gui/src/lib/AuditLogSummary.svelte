<!-- src/lib/AuditLogSummary.svelte -->
<script lang="ts">
  export let auditLog = [];
  export let total = 0;
</script>

{#if auditLog.length}
  <div class="mt-6 p-4 rounded-xl bg-blue-50 border border-blue-200 dark:bg-blue-900 dark:border-blue-800">
    <div class="font-semibold text-blue-800 dark:text-blue-200 mb-2">
      {total} remplacement{sIf(total > 1, 's')} au total
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
