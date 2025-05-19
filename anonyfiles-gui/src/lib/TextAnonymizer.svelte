<script>
  import { invoke } from '@tauri-apps/api/tauri';

  // Props pour du drag & drop ou autre (optionnel)
  export let fileContent = '';

  let inputText = '';
  let outputText = '';
  let errorMessage = '';
  let isLoading = false;
  let showCopiedToast = false;

  // Liste des options dynamiques (à synchroniser avec main.rs)
  let options = [
    { key: 'anonymizePersons', label: 'Personnes (PER)', default: true },
    { key: 'anonymizeLocations', label: 'Lieux (LOC)', default: false },
    { key: 'anonymizeOrgs', label: 'Organisations (ORG)', default: false },
    { key: 'anonymizeEmails', label: 'Emails', default: false },
    { key: 'anonymizeDates', label: 'Dates', default: false }
    // Ajoute d'autres ici si besoin
  ];

  // Construction automatique de l’état sélectionné
  let selected = {};
  options.forEach(opt => selected[opt.key] = opt.default);

  // MAJ auto quand on droppe un fichier (optionnel)
  $: if (fileContent) {
    inputText = fileContent;
    outputText = '';
    errorMessage = '';
  }

  async function anonymize() {
    if (!inputText.trim()) return;
    isLoading = true;
    outputText = '';
    errorMessage = '';

    // Construction dynamique du config à envoyer à Rust
    // { anonymizePersons: true, anonymizeLocations: false, ... }
    let config = {};
    for (const opt of options) {
      config[opt.key] = !!selected[opt.key];
    }

    try {
      const result = await invoke('anonymize_text', { input: inputText, config });
      outputText = result;
    } catch (error) {
      errorMessage = typeof error === 'object' ? JSON.stringify(error, null, 2) : String(error);
    } finally {
      isLoading = false;
    }
  }

  function copyResult() {
    if (outputText) {
      navigator.clipboard.writeText(outputText);
      showCopiedToast = true;
      setTimeout(() => showCopiedToast = false, 1600);
    }
  }
</script>

<div class="flex flex-col gap-4">
  <textarea
    class="border border-zinc-600 bg-zinc-950 text-zinc-100 p-3 rounded-lg resize-y min-h-[100px] text-base focus:outline-none focus:ring-2 focus:ring-blue-400 placeholder:text-zinc-300 transition"
    bind:value={inputText}
    placeholder="Texte à anonymiser"
    rows="6"
  ></textarea>

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
    on:click={anonymize} disabled={isLoading}
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
      <div class="flex items-center gap-2 mb-1">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
        <span class="font-bold text-green-700">Texte anonymisé :</span>
      </div>
      <textarea
        class="bg-green-50 text-green-900 p-3 rounded-lg resize-y min-h-[60px] border border-green-300 font-mono"
        readonly
        bind:value={outputText}
        rows="4"
      />
      <button
        class="self-end px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-xs"
        on:click={copyResult}
        type="button"
      >
        Copier
      </button>
      {#if showCopiedToast}
        <span class="absolute bottom-2 right-20 bg-green-600 text-white px-2 py-1 rounded shadow text-xs animate-fade-in">
          Copié !
        </span>
      {/if}
    </div>
  {/if}

  {#if errorMessage}
    <div class="border border-red-400 bg-red-950 text-red-200 rounded-lg p-3 mt-2">
      <strong>Erreur lors de l’anonymisation :</strong>
      <pre class="whitespace-pre-wrap text-xs">{errorMessage}</pre>
    </div>
  {/if}
</div>

<style>
  @keyframes fade-in {
    0% { opacity: 0; transform: translateY(12px);}
    60% { opacity: 1; transform: translateY(0);}
    100% { opacity: 0; }
  }
  .animate-fade-in {
    animation: fade-in 1.2s ease-in;
  }
</style>
