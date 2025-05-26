<script lang="ts">
  import DropZone from './DropZone.svelte';
  import CsvPreview from './CsvPreview.svelte';
  import XlsxPreview from './XlsxPreview.svelte';

  let fileName = "";
  let fileContent: string | ArrayBuffer = "";
  let fileType = ""; // "csv" | "xlsx" | "txt"

  async function handleFiles(files: FileList) {
    if (!files || files.length === 0) return;
    const file = files[0];
    fileName = file.name;

    if (file.type === "text/csv" || file.name.endsWith(".csv")) {
      fileContent = await file.text();
      fileType = "csv";
    } else if (
      file.type === "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" ||
      file.name.endsWith(".xlsx")
    ) {
      fileContent = await file.arrayBuffer();
      fileType = "xlsx";
    } else if (
      file.type === "text/plain" ||
      file.name.endsWith(".txt")
    ) {
      fileContent = await file.text();
      fileType = "txt";
    } else {
      fileContent = "";
      fileType = "";
      fileName = "";
      alert("Format de fichier non supporté.");
    }
  }
</script>

<DropZone onDrop={handleFiles} label="Déposez ici un .txt, .csv ou .xlsx, ou cliquez pour parcourir" accept=".txt,.csv,.xlsx" />

{#if fileName}
  <div class="flex items-center gap-2 text-zinc-400 text-sm mb-2">
    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 002.828 2.828l6.586-6.586A2 2 0 1015.172 7z"/>
    </svg>
    <span class="truncate max-w-[240px]">{fileName}</span>
  </div>
{/if}

{#if fileType === "csv"}
  <CsvPreview {fileContent} />
{:else if fileType === "xlsx"}
  <XlsxPreview {fileContent} />
{:else if fileType === "txt"}
  <div class="border border-gray-300 bg-gray-100 text-gray-900 p-2 rounded mb-2 text-xs max-h-40 overflow-auto whitespace-pre-line">
    {fileContent}
  </div>
{:else if fileName}
  <div class="text-red-500">Format non supporté pour l’aperçu.</div>
{/if}
