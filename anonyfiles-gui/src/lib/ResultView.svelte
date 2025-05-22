<script lang="ts">
  export let inputText = "";
  export let outputText = "";
  export let showSplitView = true;
  export let showOriginal = false;
  export let copied = false;

  export let onToggleSplitView = () => {};
  export let onToggleShowOriginal = () => {};
  export let onCopyOutput = () => {};
  export let onExportOutput = () => {};
</script>

{#if outputText}
<div class="border border-green-200 bg-green-50 text-green-900 rounded-2xl p-4 flex flex-col gap-2 mt-4 shadow-sm dark:border-green-800 dark:bg-green-900 dark:text-green-200">
    <div class="flex items-center gap-4 mb-2">
        <span class="font-bold text-lg flex-1">
            Aperçu {showSplitView ? "Avant / Après" : (showOriginal ? "Original" : "Anonymisé")}
        </span>
        <button
            class="px-4 py-1 rounded-md bg-zinc-200 hover:bg-zinc-300 font-medium text-zinc-800 transition mr-2 dark:bg-gray-600 dark:hover:bg-gray-500 dark:text-zinc-100"
            on:click={onToggleSplitView}
            type="button"
        >
            {showSplitView ? "Vue unique" : "Vue Avant/Après"}
        </button>
        {#if !showSplitView}
            <button
                class="px-3 py-1 rounded bg-blue-600 hover:bg-blue-700 text-white font-semibold ml-2"
                on:click={onToggleShowOriginal}
                type="button"
            >
                {showOriginal ? "Voir anonymisé" : "Voir original"}
            </button>
        {/if}
    </div>
    {#if showSplitView}
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="flex flex-col">
                <span class="mb-1 font-semibold text-zinc-600 dark:text-zinc-300">Texte original</span>
                <textarea
                    class="bg-white text-zinc-900 p-3 rounded-xl resize-y min-h-[60px] border border-zinc-300 font-mono w-full dark:bg-gray-800 dark:text-zinc-100 dark:border-gray-600"
                    readonly
                    value={inputText}
                    rows="6"
                />
            </div>
            <div class="flex flex-col">
                <span class="mb-1 font-semibold text-green-800 dark:text-green-300">Texte anonymisé</span>
                <textarea
                    class="bg-green-50 text-green-900 p-3 rounded-xl resize-y min-h-[60px] border border-green-200 font-mono w-full dark:bg-green-800 dark:text-green-100 dark:border-green-700"
                    readonly
                    value={outputText}
                    rows="6"
                />
                <div class="flex gap-2 justify-end mt-2">
                    <button
                        class="flex items-center gap-1 px-4 py-1.5 rounded-md bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow transition disabled:opacity-60"
                        type="button"
                        on:click={onCopyOutput}
                        disabled={copied}
                    >
                        {#if copied}
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
                    <button
                        class="flex items-center gap-1 px-4 py-1.5 rounded-md bg-green-700 hover:bg-green-800 text-white font-semibold shadow transition"
                        type="button"
                        on:click={onExportOutput}
                    >
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
                class={showOriginal
                    ? "bg-white text-zinc-900 p-3 rounded-xl resize-y min-h-[60px] border border-zinc-300 font-mono w-full dark:bg-gray-800 dark:text-zinc-100 dark:border-gray-600"
                    : "bg-green-50 text-green-900 p-3 rounded-xl resize-y min-h-[60px] border border-green-200 font-mono w-full dark:bg-green-800 dark:text-green-100 dark:border-green-700"}
                readonly
                value={showOriginal ? inputText : outputText}
                rows="6"
            />
            {#if !showOriginal}
                <div class="flex gap-2 justify-end mt-2">
                    <button
                        class="flex items-center gap-1 px-4 py-1.5 rounded-md bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow transition disabled:opacity-60"
                        type="button"
                        on:click={onCopyOutput}
                        disabled={copied}
                    >
                        {#if copied}
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
                    <button
                        class="flex items-center gap-1 px-4 py-1.5 rounded-md bg-green-700 hover:bg-green-800 text-white font-semibold shadow transition"
                        type="button"
                        on:click={onExportOutput}
                    >
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
