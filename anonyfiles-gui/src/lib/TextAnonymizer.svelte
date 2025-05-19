<script lang="ts">
  import { invoke } from '@tauri-apps/api/tauri';

  export let inputText = "";
  export let fileType = "";      // "csv", "xlsx", ou "txt"
  export let hasHeader = true;   // "ligne d’en-tête"
  export let xlsxFileLoaded = false; // <--- Ajout clé

  let outputText = "";
  let isLoading = false;
  let errorMessage = "";

  let options = [
    { key: 'anonymizePersons', label: 'Personnes (PER)', default: true },
    { key: 'anonymizeLocations', label: 'Lieux (LOC)', default: false },
    { key: 'anonymizeOrgs', label: 'Organisations (ORG)', default: false },
    { key: 'anonymizeEmails', label: 'Emails', default: false },
    { key: 'anonymizeDates', label: 'Dates', default: false }
  ];
  let selected = {};
  options.forEach(opt => selected[opt.key] = opt.default);

  // Logique du bouton
  $: canAnonymize =
    (fileType === "txt" && inputText.trim()) ||
    (fileType === "csv" && inputText.trim()) ||
    (fileType === "xlsx" && xlsxFileLoaded);

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
</script>

<div class="flex flex-wrap gap-4 mb-2">
  {#each options as opt}
    <div class="flex items-center gap-2">
      <input
        type="checkbox"
        id={opt.key}
        bind:checked={selected[opt.key]}
        class="w-5 h-5 text-blue-600 rounded border-zinc-400 focus:ring-blue-400 bg-zinc-950"
      />
      <label for={opt.key} class="select-none text-zinc-200 text-base">
        {opt.label}
      </label>
    </div>
  {/each}
</div>

<button
  class="px-6 py-3 font-semibold text-white rounded-xl bg-blue-600 hover:bg-blue-700 active:bg-blue-800 shadow-md transition-all disabled:bg-gray-400 disabled:cursor-wait mt-2 flex items-center justify-center gap-2"
  on:click={anonymize}
  disabled={isLoading || !canAnonymize}
>
  {#if isLoading}
    <svg class="animate-spin h-5 w-5 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
    </svg>
    Traitement en cours…
  {:else}
    Anonymiser
  {/if}
</button>

{#if outputText}
  <div class="border border-green-400 bg-green-100 text-green-800 rounded-lg p-4 flex flex-col gap-2 mt-2 relative">
    <span class="font-bold text-green-700">Texte anonymisé :</span>
    <textarea
      class="bg-green-50 text-green-900 p-3 rounded-lg resize-y min-h-[60px] border border-green-300 font-mono"
      readonly
      bind:value={outputText}
      rows="4"
    />
  </div>
{/if}

{#if errorMessage}
  <div class="border border-red-400 bg-red-950 text-red-200 rounded-lg p-3 mt-2">
    <strong>Erreur lors de l’anonymisation :</strong>
    <pre class="whitespace-pre-wrap text-xs">{errorMessage}</pre>
  </div>
{/if}
