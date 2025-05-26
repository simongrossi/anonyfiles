<script lang="ts">
  export let headers: string[] = [];
  export let rows: string[][] = [];
  export let hasHeader: boolean = true;
</script>

<div class="overflow-x-auto mb-4">
  <table class="min-w-full text-sm border border-zinc-300 bg-white rounded-xl">
    {#if hasHeader}
      <thead>
        <tr>
          {#each headers as col}
            <th class="px-2 py-1 border-b border-zinc-200 bg-blue-50 text-blue-700 font-bold">{col}</th>
          {/each}
        </tr>
      </thead>
      <tbody>
        {#each rows as row}
          <tr>
            {#each row as cell}
              <td class="px-2 py-1 border-b border-zinc-100 text-zinc-700">{cell}</td>
            {/each}
          </tr>
        {/each}
      </tbody>
    {:else}
      <tbody>
        {#each [headers, ...rows] as row}
          <tr>
            {#each row as cell}
              <td class="px-2 py-1 border-b border-zinc-100 text-zinc-700">{cell}</td>
            {/each}
          </tr>
        {/each}
      </tbody>
    {/if}
  </table>
  <div class="text-xs text-zinc-500 mt-1">
    (Aperçu des {hasHeader ? rows.length : rows.length + 1} premières lignes)
  </div>
</div>
