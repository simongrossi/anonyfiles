<script lang="ts">
  import Papa from "papaparse";
  export let fileContent: string = "";
  export let hasHeader: boolean = true;

  let rows: string[][] = [];

  $: if (fileContent) {
    const result = Papa.parse(fileContent.trim(), { delimiter: ",", skipEmptyLines: true });
    rows = (result.data as string[][]).slice(0, 10);
  }
</script>

{#if rows.length > 0}
  <div class="overflow-x-auto my-2">
    <table class="min-w-full text-xs border border-blue-800 rounded-lg shadow">
      <tbody>
        {#each rows as row, i}
          <tr class={
              hasHeader && i === 0
              ? "font-bold bg-blue-900 text-blue-200"
              : (i % 2 === 0 ? "bg-zinc-900 text-zinc-200" : "bg-zinc-800 text-zinc-200")
            }>
            {#each row as cell}
              <td class="border border-blue-900 px-2 py-1">{cell}</td>
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>
    {#if rows.length === 10}
      <div class="text-xs text-blue-400 mt-1">Aperçu limité à 10 lignes…</div>
    {/if}
  </div>
{:else}
  <div class="text-blue-400">Aucun contenu CSV à prévisualiser.</div>
{/if}
