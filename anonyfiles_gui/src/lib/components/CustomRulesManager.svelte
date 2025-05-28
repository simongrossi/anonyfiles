<!-- #anonyfiles/anonyfiles_gui/src/lib/components/CustomRulesManager.svelte -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let currentRules: { pattern: string, replacement: string, isRegex?: boolean }[] = [];
  export let error: string = "";

  const dispatch = createEventDispatcher();

  let newPattern = "";
  let newReplacement = "";
  let newIsRegex = false;

  function addRule() {
    if (!newPattern.trim()) return;
    dispatch('addrule', { pattern: newPattern, replacement: newReplacement, isRegex: newIsRegex });
    newPattern = "";
    newReplacement = "";
    newIsRegex = false;
  }

  function removeRule(idx: number) {
    dispatch('removerule', idx);
  }

  function clearAllRules() {
    dispatch('clearall');
  }
</script>

<div class="bg-white dark:bg-zinc-800 rounded-xl p-4 shadow space-y-4">
  <div class="flex justify-between items-center">
    <h3 class="font-semibold text-blue-600 dark:text-blue-300 text-sm">
      Règles de remplacement personnalisées
    </h3>
    {#if currentRules.length > 0}
      <button
        type="button"
        on:click={clearAllRules}
        class="text-xs text-gray-500 hover:text-red-600 underline underline-offset-2 transition"
        title="Réinitialiser toutes les règles"
      >
        🧹 Réinitialiser
      </button>
    {/if}
  </div>

  <!-- Formulaire -->
  <div class="flex flex-col sm:flex-row gap-2 sm:items-center">
    <input
      type="text"
      placeholder="Motif à remplacer"
      bind:value={newPattern}
      on:keydown={(e) => { if (e.key === 'Enter') addRule(); }}
      class="w-full sm:w-40 px-3 py-2 text-sm border border-zinc-300 dark:border-zinc-600 rounded font-mono"
    />
    <span class="hidden sm:inline text-gray-400 text-lg">→</span>
    <input
      type="text"
      placeholder="Remplacement"
      bind:value={newReplacement}
      on:keydown={(e) => { if (e.key === 'Enter') addRule(); }}
      class="w-full sm:w-40 px-3 py-2 text-sm border border-zinc-300 dark:border-zinc-600 rounded font-mono"
    />
    <label class="flex items-center gap-1 text-xs text-blue-700 dark:text-blue-300">
      <input type="checkbox" bind:checked={newIsRegex} class="accent-blue-600" />
      Regex
    </label>
    <button
      type="button"
      class="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 active:bg-blue-800 disabled:opacity-40"
      on:click={addRule}
      disabled={!newPattern.trim()}
      title="Ajouter la règle"
    >Ajouter</button>
  </div>

  {#if error}
    <div class="text-sm text-red-600 italic">{error}</div>
  {/if}

  <!-- Liste des règles -->
  <ul class="space-y-2">
    {#each currentRules as rule, i}
      <li class="flex justify-between items-center bg-gray-100 dark:bg-zinc-700 px-3 py-2 rounded">
        <div class="text-sm break-all text-blue-900 dark:text-blue-100">
          <code>{rule.pattern}</code>
          {#if rule.isRegex}
            <span class="ml-1 px-2 py-0.5 rounded text-xs bg-blue-200 text-blue-800 dark:bg-blue-800 dark:text-blue-200">regex</span>
          {/if}
          <span class="mx-1 text-gray-500">→</span>
          <code class="font-mono">{rule.replacement}</code>
        </div>
        <button
          class="ml-4 px-2 py-1 bg-red-100 text-red-600 text-xs rounded hover:bg-red-300 dark:bg-red-800 dark:text-red-200 dark:hover:bg-red-700"
          type="button"
          on:click={() => removeRule(i)}
          title="Supprimer cette règle"
        >
          ✕
        </button>
      </li>
    {/each}
    {#if !currentRules.length}
      <li class="italic text-gray-400 text-xs">Aucune règle personnalisée</li>
    {/if}
  </ul>
</div>
