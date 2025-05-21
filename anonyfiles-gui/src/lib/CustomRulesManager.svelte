<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let currentRules: { pattern: string, replacement: string, isRegex?: boolean }[] = [];
  export let error: string = "";

  const dispatch = createEventDispatcher();

  // Nouveaux champs pour la création de règle
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
</script>

<div class="flex flex-col gap-4">
  <div class="flex items-center gap-2">
    <input
      type="text"
      class="w-40 px-2 py-1 border border-zinc-300 rounded-md text-sm font-mono"
      placeholder="Motif à remplacer"
      bind:value={newPattern}
      on:keydown={(e) => { if (e.key === 'Enter') addRule(); }}
    />
    <span class="text-gray-400 text-lg">→</span>
    <input
      type="text"
      class="w-40 px-2 py-1 border border-zinc-300 rounded-md text-sm font-mono"
      placeholder="Remplacement"
      bind:value={newReplacement}
      on:keydown={(e) => { if (e.key === 'Enter') addRule(); }}
    />
    <label class="flex items-center gap-1 ml-3">
      <input type="checkbox" bind:checked={newIsRegex} class="accent-blue-600" />
      <span class="text-xs text-blue-700 dark:text-blue-300">Regex avancée</span>
    </label>
    <button
      type="button"
      class="ml-2 px-3 py-1 bg-primary text-white rounded shadow-sm hover:bg-blue-800 active:bg-blue-900 transition"
      on:click={addRule}
      disabled={!newPattern.trim()}
      title="Ajouter la règle"
    >Ajouter</button>
  </div>
  {#if error}
    <div class="text-sm text-red-600 italic">{error}</div>
  {/if}
  <ul class="space-y-1">
    {#each currentRules as rule, i}
      <li class="flex items-center gap-2 bg-blue-50 dark:bg-blue-900/40 p-2 rounded">
        <span class="flex-1 break-all text-blue-900 dark:text-blue-100">
          {rule.pattern}
          {#if rule.isRegex}
            <span class="ml-1 px-2 py-0.5 rounded text-xs bg-blue-200 text-blue-900 dark:bg-blue-800 dark:text-blue-200">regex</span>
          {/if}
          <span class="mx-1 text-gray-400">→</span>
          <span class="font-mono">{rule.replacement}</span>
        </span>
        <button
          class="ml-2 px-2 py-1 rounded bg-red-100 text-red-700 hover:bg-red-300 dark:bg-red-800 dark:text-red-200 dark:hover:bg-red-700 text-xs"
          type="button"
          on:click={() => removeRule(i)}
          title="Supprimer la règle"
        >✕</button>
      </li>
    {/each}
    {#if !currentRules.length}
      <li class="italic text-gray-400 text-xs px-2 py-1">Aucune règle personnalisée</li>
    {/if}
  </ul>
</div>
