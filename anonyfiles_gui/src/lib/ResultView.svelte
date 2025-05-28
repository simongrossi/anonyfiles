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
  export let onExportMapping = () => {}; // Ajouté

  const dispatch = createEventDispatcher();

  $: totalReplacements = auditLog?.reduce?.((s, l) => s + (l.count || 0), 0) ?? 0;

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
              ✅ Copié !
            {:else}
              📋 Copier
            {/if}
          </button>
          <button class="btn-success" type="button" on:click={onExportOutput} disabled={isLoading}>💾 Exporter</button>
          <button class="btn-success" type="button" on:click={onExportMapping} disabled={isLoading}>📑 Exporter Mapping</button>
          <button on:click={handleShowLog} class="btn-secondary" disabled={isLoading}>🪵 Voir le log</button>
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
              ✅ Copié !
            {:else}
              📋 Copier
            {/if}
          </button>
        {/if}
        <button class="btn-success" type="button" on:click={onExportOutput} disabled={isLoading}>💾 Exporter</button>
        <button class="btn-success" type="button" on:click={onExportMapping} disabled={isLoading}>📑 Exporter Mapping</button>
        <button on:click={handleShowLog} class="btn-secondary" disabled={isLoading}>🪵 Voir le log</button>
      </div>
    </div>
  {/if}
</div>
{/if}
