<script lang="ts">
  import { copyTextToClipboard } from './clipboard'; // <-- utilitaire
  export let inputText = "";
  export let outputText = "";
  export let showSplitView = true;
  export let showOriginal = false;
  export let copied = false;

  export let onToggleSplitView = () => {};
  export let onToggleShowOriginal = () => {};
  // export let onCopyOutput = () => {}; // On ne s'en sert plus directement
  export let onExportOutput = () => {};

  // On gère l'état "copié" localement ici (optionnel : tu peux lever un event au parent si besoin)
  let localCopied = false;
  let copyTimeout: ReturnType<typeof setTimeout> | null = null;

  async function handleCopyOutput() {
    const ok = await copyTextToClipboard(outputText);
    if (ok) {
      localCopied = true;
      // Reset après 1,5s
      if (copyTimeout) clearTimeout(copyTimeout);
      copyTimeout = setTimeout(() => { localCopied = false; }, 1500);
    } else {
      alert("Impossible de copier le texte. Vérifiez les permissions.");
    }
  }
</script>

{#if outputText}
<div class="card-panel card-success mt-4 flex flex-col gap-2 shadow-sm">
    <div class="flex items-center gap-4 mb-2">
        <span class="font-bold text-lg flex-1">
            Aperçu {showSplitView ? "Avant / Après" : (showOriginal ? "Original" : "Anonymisé")}
        </span>
        <button class="btn-toggle" on:click={onToggleSplitView} type="button">
            {showSplitView ? "Vue unique" : "Vue Avant/Après"}
        </button>
        {#if !showSplitView}
            <button class="btn-toggle-alt" on:click={onToggleShowOriginal} type="button">
                {showOriginal ? "Voir anonymisé" : "Voir original"}
            </button>
        {/if}
    </div>
    {#if showSplitView}
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="flex flex-col">
                <span class="mb-1 font-semibold text-zinc-600 dark:text-zinc-300">Texte original</span>
                <textarea
                    class="input-text bg-white dark:bg-gray-800 dark:text-zinc-100 dark:border-gray-600"
                    readonly
                    value={inputText}
                    rows="6"
                />
            </div>
            <div class="flex flex-col">
                <span class="mb-1 font-semibold text-green-800 dark:text-green-300">Texte anonymisé</span>
                <textarea
                    class="input-text bg-green-50 text-green-900 border-green-200 dark:bg-green-800 dark:text-green-100 dark:border-green-700"
                    readonly
                    value={outputText}
                    rows="6"
                />
                <div class="flex gap-2 justify-end mt-2">
                    <button class="btn-copy" type="button" on:click={handleCopyOutput} disabled={localCopied}>
                        {#if localCopied}
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                            </svg>
                            Copié !
                        {:else}
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <rect x="9" y="9" width="13" height="13" rx="2" stroke="currentColor" stroke-width="2"/>
                                <rect x="3" y="3" width="13" height="13" rx="2" stroke="currentColor" stroke-width="2"/>
                            </svg>
                            Copier
                        {/if}
                    </button>
                    <button class="btn-success" type="button" on:click={onExportOutput}>
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v16h16V4H4zm4 8h8m-4-4v8"/>
                        </svg>
                        Exporter
                    </button>
                </div>
            </div>
        </div>
    {:else}
        <div class="flex flex-col gap-2">
            <span class="mb-1 font-semibold dark:text-zinc-200">{showOriginal ? "Texte original" : "Texte anonymisé"}</span>
            <textarea
                class="input-text {showOriginal
                    ? 'bg-white dark:bg-gray-800 dark:text-zinc-100 dark:border-gray-600'
                    : 'bg-green-50 text-green-900 border-green-200 dark:bg-green-800 dark:text-green-100 dark:border-green-700'}"
                readonly
                value={showOriginal ? inputText : outputText}
                rows="6"
            />
            {#if !showOriginal}
                <div class="flex gap-2 justify-end mt-2">
                    <button class="btn-copy" type="button" on:click={handleCopyOutput} disabled={localCopied}>
                        {#if localCopied}
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                            </svg>
                            Copié !
                        {:else}
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <rect x="9" y="9" width="13" height="13" rx="2" stroke="currentColor" stroke-width="2"/>
                                <rect x="3" y="3" width="13" height="13" rx="2" stroke="currentColor" stroke-width="2"/>
                            </svg>
                            Copier
                        {/if}
                    </button>
                    <button class="btn-success" type="button" on:click={onExportOutput}>
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v16h16V4H4zm4 8h8m-4-4v8"/>
                        </svg>
                        Exporter
                    </button>
                </div>
            {/if}
        </div>
    {/if}
</div>
{/if}
