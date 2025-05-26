<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { copyTextToClipboard } from './clipboard';

  export let inputText = "";
  export let outputText = "";
  export let auditLog = [];
  export let showSplitView = false;
  export let showOriginal = false;
  export let isLoading = false;
  export let onToggleSplitView = () => {};
  export let onToggleShowOriginal = () => {};
  export let onCopyOutput = () => {};
  export let onExportOutput = () => {};

  const dispatch = createEventDispatcher();

  // Total anonymisations
  $: totalReplacements = auditLog?.reduce?.((s, l) => s + (l.count || 0), 0) ?? 0;

  // Copie locale pour feedback
  let localCopied = false;
  let copyTimeout;
  async function handleCopyOutput() {
    if (onCopyOutput) await onCopyOutput();
    localCopied = true;
    if (copyTimeout) clearTimeout(copyTimeout);
    copyTimeout = setTimeout(() => { localCopied = false; }, 1500);
  }

  function handleShowLog() {
    dispatch('showLog');
  }
</script>

{#if outputText}
<div class="card-panel card-success mt-4 flex flex-col gap-2 shadow-sm">
  <div class="flex items-center gap-4 mb-2">
    <span class="font-bold text-lg flex-1">
      Aperçu {showSplitView ? "Avant / Après" : (showOriginal ? "Original" : "Anonymisé")}
    </span>
    <span class="bg-primary/10 text-primary px-3 py-1 rounded-xl font-semibold">
      Total anonymisations : {totalReplacements}
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
          <button class="btn-copy" type="button" on:click={handleCopyOutput} disabled={localCopied || isLoading}>
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
          <button class="btn-success" type="button" on:click={onExportOutput} disabled={isLoading}>
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v16h16V4H4zm4 8h8m-4-4v8"/>
            </svg>
            Exporter
          </button>
          <button
            on:click={handleShowLog}
            class="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-200 transition flex items-center gap-2"
            disabled={isLoading}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24"><path fill="currentColor" d="M7 7h10v2H7zm0 4h7v2H7z"/><path fill="currentColor" d="M5 3a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h7v-2H5V5h14v6h2V5a2 2 0 0 0-2-2H5zm14.5 11.5a.75.75 0 0 0-1.06 0l-4.72 4.72a.75.75 0 0 0-.22.53v2.25c0 .41.34.75.75.75h2.25a.75.75 0 0 0 .53-.22l4.72-4.72a.75.75 0 0 0 0-1.06l-2.25-2.25zm-4.03 5.09.75-.75 2.25 2.25-.75.75H16.5v-2.25z"/></svg>
            Voir le log
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
      <div class="flex gap-2 justify-end mt-2">
        {#if !showOriginal}
          <button class="btn-copy" type="button" on:click={handleCopyOutput} disabled={localCopied || isLoading}>
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
        {/if}
        <button class="btn-success" type="button" on:click={onExportOutput} disabled={isLoading}>
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v16h16V4H4zm4 8h8m-4-4v8"/>
          </svg>
          Exporter
        </button>
        <button
          on:click={handleShowLog}
          class="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-200 transition flex items-center gap-2"
          disabled={isLoading}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24"><path fill="currentColor" d="M7 7h10v2H7zm0 4h7v2H7z"/><path fill="currentColor" d="M5 3a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h7v-2H5V5h14v6h2V5a2 2 0 0 0-2-2H5zm14.5 11.5a.75.75 0 0 0-1.06 0l-4.72 4.72a.75.75 0 0 0-.22.53v2.25c0 .41.34.75.75.75h2.25a.75.75 0 0 0 .53-.22l4.72-4.72a.75.75 0 0 0 0-1.06l-2.25-2.25zm-4.03 5.09.75-.75 2.25 2.25-.75.75H16.5v-2.25z"/></svg>
          Voir le log
        </button>
      </div>
    </div>
  {/if}
</div>
{/if}
