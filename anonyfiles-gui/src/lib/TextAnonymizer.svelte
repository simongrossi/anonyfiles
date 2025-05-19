<script>
  import { invoke } from '@tauri-apps/api/tauri';

  export let fileContent = '';
  let inputText = '';
  let outputText = '';
  let errorMessage = '';
  let isLoading = false;
  let anonymizePersons = true;

  async function anonymize() {
    if (!inputText.trim()) return;
    isLoading = true;
    outputText = '';
    errorMessage = '';

    const config = { anonymizePersons };
    try {
      const result = await invoke('anonymize_text', { input: inputText, config });
      outputText = result;
    } catch (error) {
      errorMessage = typeof error === 'object' ? JSON.stringify(error, null, 2) : String(error);
    } finally {
      isLoading = false;
    }
  }

  $: if (fileContent) {
    inputText = fileContent;
    outputText = '';
    errorMessage = '';
  }
</script>

<div class="bg-zinc-900 rounded-xl p-6 shadow-lg flex flex-col gap-4 border border-zinc-700">
  <textarea
    class="border border-zinc-600 bg-zinc-950 text-white p-3 rounded-lg resize-y min-h-[100px] text-base focus:outline-none focus:ring-2 focus:ring-blue-400"
    bind:value={inputText}
    placeholder="Texte à anonymiser"
    rows="6"
  ></textarea>

  <div class="flex items-center gap-2">
    <input type="checkbox" id="anonymizePersons" bind:checked={anonymizePersons}
      class="w-5 h-5 text-blue-600 rounded border-zinc-400 focus:ring-blue-400 bg-zinc-950" />
    <label for="anonymizePersons" class="select-none text-zinc-200 text-base">
      Anonymiser les personnes (PER)
    </label>
  </div>

  <button
    class="px-6 py-3 font-semibold text-white rounded-lg bg-blue-600 hover:bg-blue-700 active:bg-blue-800 transition disabled:bg-gray-400 disabled:cursor-wait mt-2"
    on:click={anonymize} disabled={isLoading}
  >
    {isLoading ? 'Traitement en cours…' : 'Anonymiser'}
  </button>

  {#if outputText}
    <textarea
      class="border border-green-400 bg-green-950 text-green-200 p-3 rounded-lg resize-y min-h-[80px] text-base mt-2"
      bind:value={outputText}
      placeholder="Texte anonymisé"
      rows="6"
      readonly
    ></textarea>
  {/if}

  {#if errorMessage}
    <div class="border border-red-400 bg-red-950 text-red-300 rounded-lg p-3 mt-2">
      <strong>Erreur lors de l’anonymisation :</strong>
      <pre class="whitespace-pre-wrap text-xs">{errorMessage}</pre>
    </div>
  {/if}
</div>
