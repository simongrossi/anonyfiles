<script lang="ts">
  export let headers: string[] = [];
  export let rows: string[][] = [];
  export let hasHeader: boolean = true;
</script>

<div class="overflow-x-auto mb-4 rounded-xl border border-zinc-200 dark:border-zinc-700">
  <table class="min-w-full text-sm bg-white dark:bg-zinc-900">
    {#if hasHeader}
      <thead>
        <tr>
          {#each headers as col}
            <th class="px-2 py-1 border-b border-zinc-200 dark:border-zinc-700 bg-brand-50 dark:bg-brand-900/30 text-brand-700 dark:text-brand-100 font-semibold text-left">{col}</th>
          {/each}
        </tr>
      </thead>
      <tbody>
        {#each rows as row}
          <tr class="hover:bg-zinc-50 dark:hover:bg-zinc-800/60">
            {#each row as cell}
              <td class="px-2 py-1 border-b border-zinc-100 dark:border-zinc-800 text-zinc-700 dark:text-zinc-200">{cell}</td>
            {/each}
          </tr>
        {/each}
      </tbody>
    {:else}
      <tbody>
        {#each [headers, ...rows] as row}
          <tr class="hover:bg-zinc-50 dark:hover:bg-zinc-800/60">
            {#each row as cell}
              <td class="px-2 py-1 border-b border-zinc-100 dark:border-zinc-800 text-zinc-700 dark:text-zinc-200">{cell}</td>
            {/each}
          </tr>
        {/each}
      </tbody>
    {/if}
  </table>
</div>
<div class="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
  (Aperçu des {hasHeader ? rows.length : rows.length + 1} premières lignes)
</div>
