<script lang="ts">
  import { invoke } from '@tauri-apps/api/tauri';

  let inputText = "";
  let outputText = "";
  let isLoading = false;
  let errorMessage = "";
  let fileType = "txt";
  let fileName = "";
  let hasHeader = true;
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

  let copied = false;
  async function copyOutput() {
    try {
      await navigator.clipboard.writeText(outputText);
      copied = true;
      setTimeout(() => copied = false, 1200);
    } catch (e) {
      alert("Impossible de copier le texte. Vérifiez les permissions.");
    }
  }

  // Export du texte anonymisé
  function exportOutput() {
    const blob = new Blob([outputText], { type: "text/plain;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    // On adapte le nom au fichier de base si possible
    const baseName = fileName ? fileName.replace(/\.[^/.]+$/, "") : "anonymized";
    link.download = `${baseName}_anonymized.txt`;
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      URL.revokeObjectURL(link.href);
      document.body.removeChild(link);
    }, 200);
  }

  $: canAnonymize =
    (fileType === "txt" && inputText.trim()) ||
    (fileType === "csv" && inputText.trim()) ||
    (fileType === "xlsx" && inputText.trim());

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
    if (ext === "txt" || ext === "csv") {
      const reader = new FileReader();
      reader.onload = (e) => {
        inputText = e.target.result as string;
      };
      reader.readAsText(file, "UTF-8");
    } else if (ext === "xlsx") {
      inputText = "";
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

{#if isLoading}
  <div class="fixed inset-0 z-50 bg-black bg-opacity-40 flex flex-col items-center justify-center">
    <div class="flex flex-col items-center gap-3 p-8 bg-white rounded-2xl shadow-xl border border-zinc-200">
      <svg class="animate-spin h-8 w-8 text-blue-700 mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
      </svg>
      <span class="font-bold text-lg text-zinc-800 text-center">
        Anonymisation en cours…
      </span>
      <span class="text-zinc-500 text-sm text-center max-w-xs">
        Pour les gros fichiers, le traitement peut prendre plusieurs secondes.<br/>
        Merci de patienter, la fenêtre reste responsive.
      </span>
    </div>
  </div>
{/if}

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

{#if fileType === "csv" || fileType === "xlsx"}
  <div class="mb-4 flex items-center gap-2">
    <input type="checkbox" id="hasHeader" bind:checked={hasHeader} class="accent-blue-600" />
    <label for="hasHeader" class="select-none text-zinc-700">Le fichier contient une ligne d’en-tête</label>
  </div>
{/if}

<div class="flex flex-wrap gap-5 mb-3 mt-1">
  {#each options as opt}
    <div class="flex items-center gap-2">
      <input
        type="checkbox"
        id={opt.key}
        bind:checked={selected[opt.key]}
        class="w-5 h-5 accent-blue-600 border-zinc-400 focus:ring-blue-400 bg-zinc-200 rounded"
        disabled={isLoading}
      />
      <label for={opt.key} class="select-none text-zinc-800 text-base font-medium">
        {opt.label}
      </label>
    </div>
  {/each}
</div>

<div class="flex gap-4 mt-2 mb-2">
  <button
    class="px-6 py-2 font-semibold text-white rounded-xl bg-blue-700 hover:bg-blue-800 active:bg-blue-900 shadow-sm transition-all disabled:bg-zinc-400 disabled:cursor-wait"
    on:click={anonymize}
    disabled={isLoading || !canAnonymize}
    aria-busy={isLoading}
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

{#if outputText}
  <div class="border border-green-200 bg-green-50 text-green-900 rounded-2xl p-4 flex flex-col gap-2 mt-4 shadow-sm">
    <span class="font-bold text-green-900">Texte anonymisé :</span>
    <textarea
      class="bg-green-50 text-green-900 p-3 rounded-xl resize-y min-h-[60px] border border-green-200 font-mono w-full"
      readonly
      bind:value={outputText}
      rows="4"
    />
    <div class="flex gap-2 justify-end mt-1">
      <button
        class="flex items-center gap-1 px-4 py-1.5 rounded-md bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-semibold shadow transition disabled:opacity-60"
        type="button"
        on:click={copyOutput}
        disabled={copied}
      >
        {#if copied}
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          Copié !
        {:else}
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <rect x="9" y="9" width="13" height="13" rx="2" stroke="currentColor" stroke-width="2"/>
            <rect x="3" y="3" width="13" height="13" rx="2" stroke="currentColor" stroke-width="2"/>
          </svg>
          Copier
        {/if}
      </button>
      <button
        class="flex items-center gap-1 px-4 py-1.5 rounded-md bg-green-700 hover:bg-green-800 active:bg-green-900 text-white font-semibold shadow transition"
        type="button"
        on:click={exportOutput}
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v16h16V4H4zm4 8h8m-4-4v8"/>
        </svg>
        Exporter
      </button>
    </div>
  </div>
{/if}

{#if errorMessage}
  <div class="border border-red-200 bg-red-50 text-red-800 rounded-xl p-3 mt-4">
    <strong>Erreur lors de l’anonymisation :</strong>
    <pre class="whitespace-pre-wrap text-xs">{errorMessage}</pre>
  </div>
{/if}
