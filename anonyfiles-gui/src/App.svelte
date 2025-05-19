<script lang="ts">
  // @ts-ignore: No type declarations for Svelte files
  import DropZone from './lib/DropZone.svelte';
  // @ts-ignore
  import CsvPreview from './lib/CsvPreview.svelte';
  // @ts-ignore
  import XlsxPreview from './lib/XlsxPreview.svelte';
  // @ts-ignore
  import TextAnonymizer from './lib/TextAnonymizer.svelte';

  let fileName = "";
  let fileContent: string | ArrayBuffer = "";
  let fileType: "csv" | "xlsx" | "txt" | "" = "";
  let inputText: string = "";
  let xlsxFileLoaded = false; // << Nouvelle variable pour l’état xlsx

  // Option "ligne d’en-tête"
  let hasHeader = true;

  async function handleFiles(files: FileList) {
    if (!files || files.length === 0) return;
    const file = files[0];
    fileName = file.name;
    hasHeader = true;
    xlsxFileLoaded = false; // reset

    if (file.type === "text/csv" || file.name.endsWith(".csv")) {
      fileContent = await file.text();
      fileType = "csv";
      inputText = fileContent as string;
    } else if (
      file.type === "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" ||
      file.name.endsWith(".xlsx")
    ) {
      fileContent = await file.arrayBuffer();
      fileType = "xlsx";
      inputText = ""; // rien à afficher/textarea
      xlsxFileLoaded = true; // ACTIVE le bouton anonymiser !
    } else if (
      file.type === "text/plain" ||
      file.name.endsWith(".txt")
    ) {
      fileContent = await file.text();
      fileType = "txt";
      inputText = fileContent as string;
    } else {
      fileContent = "";
      fileType = "";
      fileName = "";
      inputText = "";
      xlsxFileLoaded = false;
      alert("Format de fichier non supporté.");
    }
  }

  function handleManualInput(e: Event) {
    const target = e.target as HTMLTextAreaElement;
    if (!target.value) {
      fileContent = "";
      fileType = "";
      fileName = "";
      xlsxFileLoaded = false;
    }
    inputText = target.value;
  }
</script>

<svelte:head>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@700;400&display=swap" rel="stylesheet" />
</svelte:head>

<div class="min-h-screen flex flex-col items-center justify-center bg-zinc-900 font-sans">
  <div class="bg-zinc-900 rounded-2xl shadow-2xl border border-zinc-800 max-w-md w-full mx-4 mt-10 mb-10 p-8 flex flex-col gap-6">
    <!-- HEADER -->
    <div>
      <h1 class="text-3xl font-extrabold select-none" style="font-family: Inter, sans-serif;">
        <span class="text-blue-400">anonyfiles</span><span class="text-zinc-200">GUI</span>
      </h1>
      <a href="https://github.com/simongrossi" target="_blank"
         class="text-xs text-blue-300 hover:underline ml-1">@simongrossi</a>
    </div>

    <!-- DROPZONE -->
    <DropZone onDrop={handleFiles} label="Déposez un .txt, .csv ou .xlsx, ou cliquez" accept=".txt,.csv,.xlsx" />

    <!-- NOM DU FICHIER -->
    {#if fileName}
      <div class="flex items-center gap-2 text-zinc-400 text-sm mb-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 002.828 2.828l6.586-6.586A2 2 0 1015.172 7z"/>
        </svg>
        <span class="truncate max-w-[240px]">{fileName}</span>
      </div>
    {/if}

    <!-- OPTION HEADER POUR CSV/XLSX -->
    {#if (fileType === "csv" || fileType === "xlsx")}
      <div class="mb-2 flex items-center gap-2">
        <input type="checkbox" id="hasHeader" bind:checked={hasHeader} class="w-4 h-4" />
        <label for="hasHeader" class="text-zinc-200 text-sm">Ce fichier comporte une ligne d’en-tête</label>
      </div>
    {/if}

    <!-- APERÇU -->
    {#if fileType === "csv"}
      <CsvPreview fileContent={typeof fileContent === "string" ? fileContent : ""} {hasHeader} />
    {:else if fileType === "xlsx"}
      <XlsxPreview fileContent={fileContent} {hasHeader} />
    {:else}
      <textarea
        class="border border-zinc-600 bg-zinc-950 text-zinc-100 p-3 rounded-lg resize-y min-h-[100px] text-base focus:outline-none focus:ring-2 focus:ring-blue-400 placeholder:text-zinc-300 transition"
        bind:value={inputText}
        placeholder="Texte à anonymiser"
        rows="6"
        on:input={handleManualInput}
      ></textarea>
    {/if}

    <!-- OPTIONS + BOUTON + RÉSULTAT, passe xlsxFileLoaded pour activer le bouton -->
    <TextAnonymizer {inputText} {fileType} {hasHeader} {xlsxFileLoaded} />
  </div>
</div>
