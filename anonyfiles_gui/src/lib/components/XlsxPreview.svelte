<script lang="ts">
  import { onMount } from "svelte";
  import * as XLSX from "xlsx";

  export let file: File | null = null;
  export let hasHeader: boolean = true;

  let sheetNames: string[] = [];
  let selectedSheet = "";
  let previewHeaders: string[] = [];
  let previewTable: string[][] = [];
  const PREVIEW_ROW_LIMIT = 10;
  let loading = false;
  let error = "";

  // Lecture du fichier XLSX et extraction des noms de feuilles
  onMount(() => {
    if (file) {
      readXlsx(file);
    }
  });

  $: if (file) readXlsx(file);

  async function readXlsx(file: File) {
    loading = true;
    error = "";
    previewHeaders = [];
    previewTable = [];
    try {
      const data = await file.arrayBuffer();
      const workbook = XLSX.read(data, { type: "array" });
      sheetNames = workbook.SheetNames;
      selectedSheet = selectedSheet || sheetNames[0];
      extractSheetPreview(workbook, selectedSheet);
    } catch (e) {
      error = "Impossible de lire le fichier Excel.";
    }
    loading = false;
  }

  function extractSheetPreview(workbook, sheetName) {
    if (!workbook.Sheets[sheetName]) return;
    const ws = workbook.Sheets[sheetName];
    const json = XLSX.utils.sheet_to_json(ws, { header: 1 });
    // json est un array de lignes (array de arrays)
    if (json.length) {
      if (hasHeader) {
        previewHeaders = json[0].map((c) => (c !== undefined ? String(c) : ""));
        previewTable = json.slice(1, 1 + PREVIEW_ROW_LIMIT).map((row) =>
          row.map((cell) => (cell !== undefined ? String(cell) : ""))
        );
      } else {
        previewHeaders = [];
        previewTable = json.slice(0, PREVIEW_ROW_LIMIT).map((row) =>
          row.map((cell) => (cell !== undefined ? String(cell) : ""))
        );
      }
    } else {
      previewHeaders = [];
      previewTable = [];
    }
  }

  // Changement de feuille
  function handleSheetChange(e) {
    selectedSheet = e.target.value;
    const data = file;
    if (!data) return;
    file.arrayBuffer().then((data) => {
      const workbook = XLSX.read(data, { type: "array" });
      extractSheetPreview(workbook, selectedSheet);
    });
  }

  // Gestion du changement de ligne d’en-tête à la volée
  $: if (file && selectedSheet) {
    file.arrayBuffer().then((data) => {
      const workbook = XLSX.read(data, { type: "array" });
      extractSheetPreview(workbook, selectedSheet);
    });
  }
</script>

{#if loading}
  <div class="text-sm text-zinc-500 dark:text-zinc-400 mb-4">Chargement du fichier Excel…</div>
{:else if error}
  <div class="text-sm text-red-700 dark:text-red-300 mb-4">{error}</div>
{:else if previewTable.length}
  <div class="mb-3 flex items-center gap-2">
    <label for="sheetSelect" class="text-sm font-medium text-zinc-700 dark:text-zinc-200">Feuille :</label>
    <select
      id="sheetSelect"
      class="ui-input !py-1 !w-auto"
      bind:value={selectedSheet}
      on:change={handleSheetChange}
    >
      {#each sheetNames as name}
        <option value={name}>{name}</option>
      {/each}
    </select>
  </div>
  <div class="overflow-x-auto mb-2 rounded-xl border border-zinc-200 dark:border-zinc-700">
    <table class="min-w-full text-sm bg-white dark:bg-zinc-900">
      {#if hasHeader}
        <thead>
          <tr>
            {#each previewHeaders as col}
              <th class="px-2 py-1 border-b border-zinc-200 dark:border-zinc-700 bg-brand-50 dark:bg-brand-900/30 text-brand-700 dark:text-brand-100 font-semibold text-left">{col}</th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each previewTable as row}
            <tr class="hover:bg-zinc-50 dark:hover:bg-zinc-800/60">
              {#each row as cell}
                <td class="px-2 py-1 border-b border-zinc-100 dark:border-zinc-800 text-zinc-700 dark:text-zinc-200">{cell}</td>
              {/each}
            </tr>
          {/each}
        </tbody>
      {:else}
        <tbody>
          {#each previewTable as row}
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
    (Aperçu des {previewTable.length} premières lignes)
  </div>
{:else}
  <div class="text-xs text-zinc-500 dark:text-zinc-400 mt-1">Aucune donnée à prévisualiser.</div>
{/if}
