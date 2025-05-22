<script lang="ts">
  export let auditLog: Array<{
    pattern: string,
    replacement: string,
    type: string,
    count: number
  }> = [];

  export let totalReplacements: number = 0;

  let filter = '';
  let sortKey: string = 'pattern';
  let sortAsc: boolean = true;

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

<div class="card-panel card-info">
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 gap-2">
    <h2 class="text-xl font-bold mb-2 sm:mb-0">Journal d’audit</h2>
    <input
      type="text"
      placeholder="Filtrer (pattern, remplacement, type)…"
      bind:value={filter}
      class="input-text w-full sm:w-72 bg-gray-100 dark:bg-gray-800"
    />
  </div>

  <div class="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-800">
    <table class="table-base">
      <thead>
        <tr class="table-header">
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
            <tr class="table-row">
              <td class="p-3 font-mono">{entry.pattern}</td>
              <td class="p-3 font-mono">{entry.replacement}</td>
              <td class="p-3">
                <span class={entry.type === 'custom' ? 'badge-type-custom' : 'badge-type-spacy'}>
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
  {#if totalReplacements > 0}
    <div class="mt-2 text-right text-sm text-blue-900 dark:text-blue-200 font-semibold">
      Total anonymisations&nbsp;: <span class="font-bold">{totalReplacements}</span>
    </div>
  {/if}
</div>
