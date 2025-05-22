<script lang="ts">
  export let auditLog: Array<{
    pattern: string,
    replacement: string,
    type: string,
    count: number
  }> = [];

  let filter = '';
  let sortKey: string = 'pattern';
  let sortAsc: boolean = true;

  // Calcul du log filtré et trié
  $: filteredLog = auditLog
    .filter(
      (item) =>
        item.pattern.toLowerCase().includes(filter.toLowerCase()) ||
        item.replacement.toLowerCase().includes(filter.toLowerCase()) ||
        item.type.toLowerCase().includes(filter.toLowerCase())
    )
    .sort((a, b) => {
      const va = (a as any)[sortKey];
      const vb = (b as any)[sortKey];
      if (va < vb) return sortAsc ? -1 : 1;
      if (va > vb) return sortAsc ? 1 : -1;
      return 0;
    });

  function sortBy(key: string) {
    if (sortKey === key) {
      sortAsc = !sortAsc;
    } else {
      sortKey = key;
      sortAsc = true;
    }
  }
</script>

<div class="p-4 bg-white dark:bg-gray-900 rounded-2xl shadow-md">
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 gap-2">
    <h2 class="text-xl font-bold mb-2 sm:mb-0">Journal d’audit</h2>
    <input
      type="text"
      placeholder="Filtrer (pattern, remplacement, type)…"
      bind:value={filter}
      class="w-full sm:w-72 p-2 rounded-xl border border-gray-300 dark:border-gray-700 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100"
    />
  </div>

  <div class="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-800">
    <table class="min-w-full text-sm">
      <thead>
        <tr class="bg-gray-100 dark:bg-gray-800">
          <th class="p-3 cursor-pointer" on:click={() => sortBy('pattern')}>
            Motif recherché
            {#if sortKey === 'pattern'}
              {sortAsc ? ' ▲' : ' ▼'}
            {/if}
          </th>
          <th class="p-3 cursor-pointer" on:click={() => sortBy('replacement')}>
            Remplacement
            {#if sortKey === 'replacement'}
              {sortAsc ? ' ▲' : ' ▼'}
            {/if}
          </th>
          <th class="p-3 cursor-pointer" on:click={() => sortBy('type')}>
            Type
            {#if sortKey === 'type'}
              {sortAsc ? ' ▲' : ' ▼'}
            {/if}
          </th>
          <th class="p-3 cursor-pointer" on:click={() => sortBy('count')}>
            Nb occur.
            {#if sortKey === 'count'}
              {sortAsc ? ' ▲' : ' ▼'}
            {/if}
          </th>
        </tr>
      </thead>
      <tbody>
        {#if filteredLog.length === 0}
          <tr>
            <td colspan="4" class="p-4 text-center text-gray-500 dark:text-gray-400">Aucune entrée</td>
          </tr>
        {:else}
          {#each filteredLog as entry (entry.pattern + entry.replacement + entry.type)}
            <tr class="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-900">
              <td class="p-3 font-mono">{entry.pattern}</td>
              <td class="p-3 font-mono">{entry.replacement}</td>
              <td class="p-3">
                <span class="px-2 py-1 rounded-xl text-xs font-semibold {entry.type === 'custom' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'}">
                  {entry.type}
                </span>
              </td>
              <td class="p-3 text-center">{entry.count}</td>
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </div>
</div>
