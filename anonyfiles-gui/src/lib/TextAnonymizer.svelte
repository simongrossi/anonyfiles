<script lang="ts">
  import { invoke } from '@tauri-apps/api/tauri';
  import { onMount } from 'svelte';

  let inputText = "";
  let outputText = "";
  let isLoading = false;
  let errorMessage = "";
  let fileType = "txt";    // "csv", "xlsx", "txt"
  let fileName = "";
  let hasHeader = true;    // Pour CSV/XLSX
  let dragActive = false;

  let options = [
    { key: 'anonymizePersons', label: 'Personnes (PER)', default: true },
    { key: 'anonymizeLocations', label: 'Lieux (LOC)', default: false },
    { key: 'anonymizeOrgs', label: 'Organisations (ORG)', default: false },
    { key: 'anonymizeEmails', label: 'Emails', default: false },
    { key: 'anonymizeDates', label: 'Dates', default: false }
  ];
  let selected = {};
  options.forEach(opt => selected[opt.key] = opt.default);

  // Activer le bouton selon contenu ou fichier chargé
  $: canAnonymize =
    (fileType === "txt" && inputText.trim()) ||
    (fileType === "csv" && inputText.trim()) ||
    (fileType === "xlsx" && inputText.trim()); // Adapté pour évolution future

  // Drag & Drop
  function handleDrop(event) {
    event.preventDefault();
    dragActive = false;
    const file = event.dataTransfer.files[0];
    handleFile(file);
  }

  function handleDragOver(event) {
    event.preventDefault();
    dragActive = true;
  }
  function handleDragLeave(event) {
    event.preventDefault();
    dragActive = false;
  }

  function handleFileInput(event) {
    const file = event.target.files[0];
    handleFile(file);
  }

  function handleFile(file) {
    if (!file) return;
    fileName = file.name;
    const ext = file.name.split('.').pop()?.toLowerCase() || "";
    if (["txt", "csv", "xlsx"].includes(ext)) {
      fileType = ext;
    } else {
      errorMessage = "Seuls les fichiers .txt, .csv, .xlsx sont pris en charge.";
      return;
    }
    // Lecture contenu (txt, csv) : preview
    if (ext === "txt" || ext === "csv") {
      const reader = new FileReader();
      reader.onload = (e) => {
        inputText = e.target.result as string;
      };
      reader.readAsText(file, "UTF-8");
    } else if (ext === "xlsx") {
      // Pour xlsx, on ne fait que stocker le nom (prévoir le backend adapté)
      inputText = ""; // Reset
    }
    errorMessage = "";
    outputText = "";
  }

  async function anonymize() {
    if (!canAnonymize) return;
    isLoading = true;
    outputText = "";
    errorMessage = "";

    let config = {};
    for (const opt of options) {
      config[opt.key] = !!selected[opt.key];
    }
    try {
      const result = await invoke('anonymize_text', {
        input: inputText,
        config,
        file_type: fileType,
        has_header: hasHeader
      });
      outputText = result as string;
    } catch (error) {
      errorMessage = typeof error === 'object' ? JSON.stringify(error, null, 2) : String(error);
    } finally {
      isLoading = false;
    }
  }

  function resetAll() {
    inputText = "";
    outputText = "";
    fileName = "";
    fileType = "txt";
    errorMessage = "";
    hasHeader = true;
    options.forEach(opt => selected[opt.key] = opt.default);
  }
</script>

<!-- DRAG & DROP -->
<div
  class="w-full mb-6 border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center cursor-pointer transition bg-zinc-100 hover:bg-zinc-200"
  class:bg-blue-50={dragActive}
  on:drop={handleDrop}
  on:dragover={handleDragOver}
  on:dragleave={handleDragLeave}
>
  <input
    type="file"
    id="fileInput"
    accept=".txt,.csv,.xlsx"
    class="hidden"
    on:change={handleFileInput}
  />
  <label for="fileInput" class="cursor-pointer flex flex-col items-center gap-2">
    <span class="text-base font-medium text-zinc-700">Déposez un fichier ou cliquez pour parcourir</span>
    <span class="text-sm text-zinc-500">Formats supportés : .txt, .csv, .xlsx</span>
    {#if fileName}
      <span class="text-blue-800 font-semibold mt-2">{fileName}</span>
    {/if}
  </label>
</div>

<!-- ZONE DE TEXTE (saisie manuelle) -->
<div class="mb-4">
  <label for="inputText" class="font-semibold text-base text-zinc-700">Texte à anonymiser :</label>
  <textarea
    id="inputText"
    class="w-full mt-2 p-3 border border-zinc-300 rounded-xl resize-y min-h-[90px] font-mono bg-white text-zinc-900 focus:bg-white transition"
    placeholder="Collez ou saisissez votre texte ici..."
    bind:value={inputText}
    rows="4"
  ></textarea>
</div>

<!-- Pour CSV/XLSX : option d'en-tête -->
{#if fileType === "csv" || fileType === "xlsx"}
  <div class="mb-4 flex items-center gap-2">
    <input type="checkbox" id="hasHeader" bind:checked={hasHeader} class="accent-blue-600" />
    <label for="hasHeader" class="select-none text-zinc-700">Le fichier contient une ligne d’en-tête</label>
  </div>
{/if}

<!-- OPTIONS D'ANONYMISATION -->
<div class="flex flex-wrap gap-5 mb-3 mt-1">
  {#each options as opt}
    <div class="flex items-center gap-2">
      <input
        type="checkbox"
        id={opt.key}
        bind:checked={selected[opt.key]}
        class="w-5 h-5 accent-blue-600 border-zinc-400 focus:ring-blue-400 bg-zinc-200 rounded"
      />
      <label for={opt.key} class="select-none text-zinc-800 text-base font-medium">
        {opt.label}
      </label>
    </div>
  {/each}
</div>

<!-- BOUTONS -->
<div class="flex gap-4 mt-2 mb-2">
  <button
    class="px-6 py-2 font-semibold text-white rounded-xl bg-blue-700 hover:bg-blue-800 active:bg-blue-900 shadow-sm transition-all disabled:bg-zinc-400 disabled:cursor-wait"
    on:click={anonymize}
    disabled={isLoading || !canAnonymize}
  >
    {#if isLoading}
      <svg class="animate-spin h-5 w-5 mr-1 inline-block align-middle" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
      </svg>
      Traitement en cours…
    {:else}
      Anonymiser
    {/if}
  </button>
  <button
    class="px-5 py-2 rounded-lg border border-zinc-300 text-zinc-700 bg-zinc-100 hover:bg-zinc-200 transition"
    type="button"
    on:click={resetAll}
    disabled={isLoading}
  >
    Réinitialiser
  </button>
</div>

<!-- PRÉVIEW DU TEXTE ANONYMISÉ -->
{#if outputText}
  <div class="border border-green-200 bg-green-50 text-green-900 rounded-2xl p-4 flex flex-col gap-2 mt-4 shadow-sm">
    <span class="font-bold text-green-900">Texte anonymisé :</span>
    <textarea
      class="bg-green-50 text-green-900 p-3 rounded-xl resize-y min-h-[60px] border border-green-200 font-mono"
      readonly
      bind:value={outputText}
      rows="4"
    />
  </div>
{/if}

<!-- ERREUR -->
{#if errorMessage}
  <div class="border border-red-200 bg-red-50 text-red-800 rounded-xl p-3 mt-4">
    <strong>Erreur lors de l’anonymisation :</strong>
    <pre class="whitespace-pre-wrap text-xs">{errorMessage}</pre>
  </div>
{/if}
