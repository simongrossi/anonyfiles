<script lang="ts">
  import {
    inputText,
    outputText,
    mappingCSV,
    auditLog, // Ce store doit maintenant être de type AuditLogEntry[]
    outputLineCount,
    outputCharCount
  } from '../stores/anonymizationStore';
  let viewMode: 'anonymized' | 'original' | 'split' | 'mapping' = 'anonymized';

  $: hasOutput = $outputText && $outputText.trim().length > 0;

  // L'erreur TypeScript ici sera résolue si le store auditLog est correctement typé
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

    <div class="flex gap-2 mb-2 flex-wrap"> <button class="btn-secondary" on:click={() => viewMode = 'anonymized'} class:btn-active={viewMode === 'anonymized'}>Texte anonymisé</button>
      <button class="btn-secondary" on:click={() => viewMode = 'original'} class:btn-active={viewMode === 'original'}>Voir l'original</button>
      <button class="btn-secondary" on:click={() => viewMode = 'split'} class:btn-active={viewMode === 'split'}>Vue comparée</button>
      <button class="btn-secondary" on:click={() => viewMode = 'mapping'} class:btn-active={viewMode === 'mapping'}>Mapping</button>
    </div>

    {#if viewMode === 'anonymized'}
      <div>
        <div class="flex justify-between items-end mb-1">
          <label class="font-semibold text-zinc-700 dark:text-zinc-200 text-base" for="anonymized-text">Texte anonymisé</label>
          <div class="text-xs text-zinc-500 dark:text-zinc-400">
            Lignes: {$outputLineCount} | Caractères: {$outputCharCount}
          </div>
        </div>
        <pre id="anonymized-text" class="anonymized-text">{$outputText}</pre>
        <div class="buttons-container">
          <button class="btn-primary" on:click={copyOutput}>Copier</button>
          <button class="btn-secondary ml-2" on:click={exportOutput}>Exporter</button>
        </div>
      </div>
    {/if}

    {#if viewMode === 'original'}
      <div>
        <div class="flex justify-between items-end mb-1">
            <label class="font-semibold text-zinc-700 dark:text-zinc-200 text-base" for="original-text">Texte original</label>
            </div>
        <pre id="original-text" class="original-text">{$inputText}</pre>
      </div>
    {/if}

    {#if viewMode === 'split'}
      <span class="font-semibold text-zinc-700 dark:text-zinc-200 text-base mb-1">Vue comparée</span>
      <div class="split-container">
        <div>
          <div class="flex justify-between items-end mb-1">
            <span class="font-semibold text-sm text-zinc-600 dark:text-zinc-300 block">Original</span>
            </div>
          <pre class="original-text">{$inputText}</pre>
        </div>
        <div>
          <div class="flex justify-between items-end mb-1">
            <span class="font-semibold text-sm text-zinc-600 dark:text-zinc-300 block">Anonymisé</span>
            <div class="text-xs text-zinc-500 dark:text-zinc-400">
              Lignes: {$outputLineCount} | Caractères: {$outputCharCount}
            </div>
          </div>
          <pre class="anonymized-text">{$outputText}</pre>
        </div>
      </div>
    {/if}

    {#if viewMode === 'mapping'}
      <div>
        <label class="font-semibold text-zinc-700 dark:text-zinc-200 text-base mb-1" for="mapping-text">Fichier de mapping généré</label>
        <pre id="mapping-text" class="p-3 rounded bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 mb-2 whitespace-pre-wrap font-mono text-[0.9em] max-h-40 overflow-auto">{$mappingCSV || "Aucun mapping généré ou disponible."}</pre>
        {#if $mappingCSV && $mappingCSV.trim()}
            <button class="btn-secondary" on:click={exportMapping}>Exporter le mapping</button>
        {/if}
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
  .flex.justify-between.items-end {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }

  /* Styles de base (mode clair) */
  .anonymized-text, .original-text {
    background-color: var(--gray-light, #f9f9f9); 
    border: 1px solid var(--gray-border, #ccc); 
    color: var(--gray-text, #222); 
    padding: 0.75rem;
    border-radius: 0.5rem;
    max-height: 15rem; 
    overflow: auto;
    font-family: monospace;
    white-space: pre-wrap;
    word-break: break-word;
  }

  /* Style spécifique pour .anonymized-text en mode clair (thème vert) */
  .anonymized-text { 
      background-color: var(--green-light, #e6f4ea); 
      border-color: var(--green-medium, #4caf50); 
      color: var(--green-dark, #256029); 
  }

  /* Styles pour le mode sombre AVEC :global() */
  :global(.dark) .original-text { /* CORRIGÉ ICI */
    background-color: #2d3748; 
    border-color: #4a5568;   
    color: #e2e8f0;        
  }

  :global(.dark) .anonymized-text { /* CORRIGÉ ICI */
    background-color: #256029; 
    border-color: #38a169;   
    color: #c6f6d5;        
  }
</style>