<script lang="ts">
  import * as XLSX from "xlsx";
  export let fileContent: ArrayBuffer | string = "";
  export let hasHeader: boolean = true;

  let rows: any[][] = [];

  $: if (fileContent) {
    try {
      const workbook = XLSX.read(fileContent, { type: typeof fileContent === "string" ? "binary" : "array" });
      const firstSheet = workbook.SheetNames[0];
      const sheet = workbook.Sheets[firstSheet];
      const data = XLSX.utils.sheet_to_json(sheet, { header: 1 });
      rows = (data as any[][]).slice(0, 10);
    } catch (e) {
      rows = [];
    }
  }
</script>

{#if rows.length > 0}
  <div class="overflow-x-auto my-2">
    <table class="min-w-full text-xs border border-purple-800 rounded-lg shadow">
      <tbody>
        {#each rows as row, i}
          <tr class={
              hasHeader && i === 0
                ? "font-bold bg-purple-900 text-purple-200"
                : (i % 2 === 0 ? "bg-zinc-900 text-zinc-200" : "bg-zinc-800 text-zinc-200")
            }>
            {#each row as cell}
              <td class="border border-purple-900 px-2 py-1">{cell}</td>
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>
    {#if rows.length === 10}
      <div class="text-xs text-purple-400 mt-1">Aperçu limité à 10 lignes…</div>
    {/if}
  </div>
{:else}
  <div class="text-purple-400">Aucun contenu XLSX à prévisualiser.</div>
{/if}
