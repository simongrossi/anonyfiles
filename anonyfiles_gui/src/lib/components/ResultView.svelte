<!-- #anonyfiles/anonyfiles_gui/src/lib/components/ResultView.svelte -->
<script lang="ts">
  import { inputText, outputText, mappingCSV, auditLog } from '../stores/anonymizationStore';
  let viewMode: 'anonymized' | 'original' | 'split' | 'mapping' = 'anonymized';

  $: hasOutput = $outputText && $outputText.trim().length > 0;

  // Calcule le total des remplacements dans l’audit log
  $: totalReplacements = $auditLog.reduce((sum, item) => sum + (item.count || 0), 0);

  function exportOutput() {
    const blob = new Blob([$outputText], { type: "text/plain;charset=utf-8" });
    const link = document.createElement("a");
    link.download = "anonymized.txt";
    link.href = URL.createObjectURL(blob);
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      URL.revokeObjectURL(link.href);
      document.body.removeChild(link);
    }, 200);
  }

  function exportMapping() {
    if (!$mappingCSV.trim()) return;
    const blob = new Blob([$mappingCSV], { type: "text/csv;charset=utf-8" });
    const link = document.createElement("a");
    link.download = "mapping.csv";
    link.href = URL.createObjectURL(blob);
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      URL.revokeObjectURL(link.href);
      document.body.removeChild(link);
    }, 200);
  }

  async function copyOutput() {
    try {
      await navigator.clipboard.writeText($outputText);
    } catch {}
  }
</script>

{#if hasOutput}
  <div class="card shadow-lg bg-white dark:bg-zinc-950 border p-4 mt-4">
    <h3 class="font-bold text-lg mb-1 text-primary">Résultat de l'anonymisation</h3>
    <p class="mb-4 text-sm text-zinc-600 dark:text-zinc-400">
      Total substitutions effectuées : <strong>{totalReplacements}</strong>
    </p>

    <div class="flex gap-2 mb-2">
      <button class="btn-secondary" on:click={() => viewMode = 'anonymized'} class:btn-active={viewMode === 'anonymized'}>Texte anonymisé</button>
      <button class="btn-secondary" on:click={() => viewMode = 'original'} class:btn-active={viewMode === 'original'}>Voir l'original</button>
      <button class="btn-secondary" on:click={() => viewMode = 'split'} class:btn-active={viewMode === 'split'}>Vue comparée</button>
      <button class="btn-secondary" on:click={() => viewMode = 'mapping'} class:btn-active={viewMode === 'mapping'}>Mapping</button>
    </div>

    {#if viewMode === 'anonymized'}
      <div>
        <label class="font-semibold text-zinc-700 text-base mb-1" for="anonymized-text">Texte anonymisé</label>
        <pre id="anonymized-text" class="anonymized-text">{$outputText}</pre>
        <div class="buttons-container">
          <button class="btn-primary" on:click={copyOutput}>Copier</button>
          <button class="btn-secondary ml-2" on:click={exportOutput}>Exporter</button>
        </div>
      </div>
    {/if}

    {#if viewMode === 'original'}
      <div>
        <label class="font-semibold text-zinc-700 text-base mb-1" for="original-text">Texte original</label>
        <pre id="original-text" class="original-text">{$inputText}</pre>
      </div>
    {/if}

    {#if viewMode === 'split'}
      <span class="font-semibold text-zinc-700 text-base mb-1">Vue comparée</span>
      <div class="split-container">
        <div>
          <span class="font-semibold text-sm text-zinc-500 mb-1 block">Original</span>
          <pre class="original-text">{$inputText}</pre>
        </div>
        <div>
          <span class="font-semibold text-sm text-zinc-500 mb-1 block">Anonymisé</span>
          <pre class="anonymized-text">{$outputText}</pre>
        </div>
      </div>
    {/if}

    {#if viewMode === 'mapping'}
      <div>
        <label class="font-semibold text-zinc-700 text-base mb-1" for="mapping-text">Fichier de mapping généré</label>
        <pre id="mapping-text" class="p-3 rounded bg-zinc-50 mb-2 whitespace-pre-wrap font-mono text-[0.95em] max-h-40 overflow-auto">{$mappingCSV}</pre>
        <button class="btn-secondary" on:click={exportMapping}>Exporter le mapping</button>
      </div>
    {/if}
  </div>
{/if}

<style>
  .buttons-container {
    display: flex;
    justify-content: flex-end;
    margin-top: 0.5rem;
  }
  .ml-2 {
    margin-left: 0.5rem;
  }
</style>
