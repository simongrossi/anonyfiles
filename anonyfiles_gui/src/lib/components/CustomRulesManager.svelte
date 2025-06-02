<script lang="ts">
  import { customReplacementRules } from '../stores/customRulesStore';
  import { get } from 'svelte/store';

  let newPattern = '';
  let newReplacement = '';
  let isRegex = false;

  function addRule() {
    if (!newPattern.trim()) return;
    customReplacementRules.update(rules => [
      ...rules,
      {
        pattern: newPattern.trim(),
        replacement: newReplacement.trim(),
        isRegex
      }
    ]);
    newPattern = '';
    newReplacement = '';
    isRegex = false;
  }

  function removeRule(index: number) {
    customReplacementRules.update(rules =>
      rules.filter((_, i) => i !== index)
    );
  }
</script>

<style>
  .rule-entry {
    display: flex;
    flex-wrap: wrap; /* Permet le retour à la ligne sur petits écrans */
    align-items: center;
    gap: 0.5rem; /* Espace entre les éléments */
    margin-bottom: 0.5rem;
    border-bottom: 1px solid #e5e7eb; /* Tailwind gray-200 */
    padding-bottom: 0.5rem;
  }
  :global(html.dark) .rule-entry { /* Séparateur en mode sombre */
    border-bottom-color: #374151; /* Tailwind gray-700 */
  }

  .rule-entry input[type="text"] {
    flex: 1 1 150px; /* Base plus petite, permet de mieux s'adapter */
  }

  .regex-label {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    /* La couleur du texte sera gérée par Tailwind directement sur le label */
  }

  .rule-form {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1rem;
    align-items: center;
  }

  .section-title {
    /* Les styles de couleur seront gérés par Tailwind */
    font-weight: bold;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
    font-size: 1.1rem; 
  }

  .delete-btn {
    color: #ef4444; /* Rouge pour le texte du bouton supprimer (Tailwind red-500) */
    font-weight: bold;
    cursor: pointer;
    background: none;
    border: none;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
  }

  .delete-btn:hover {
    background-color: #fee2e2; /* Tailwind red-100 pour hover */
  }
  :global(html.dark) .delete-btn:hover {
    background-color: #3f2121; /* Un rouge plus sombre pour hover en dark mode, ou ajustez */
    color: #fca5a5; /* Tailwind red-300 pour le texte en hover dark */
  }
  :global(html.dark) .delete-btn {
     color: #f87171; /* Tailwind red-400 pour dark mode */
  }

</style>

<div>
  <div class="section-title text-zinc-700 dark:text-zinc-200">🔧 Règles de remplacement personnalisées</div>

  <div class="rule-form">
    <input
      type="text"
      class="border rounded p-1 text-zinc-800 bg-white dark:text-zinc-100 dark:bg-zinc-700 dark:border-zinc-600 placeholder-gray-400 dark:placeholder-gray-500"
      placeholder="Motif à remplacer"
      bind:value={newPattern}
    />
    <input
      type="text"
      class="border rounded p-1 text-zinc-800 bg-white dark:text-zinc-100 dark:bg-zinc-700 dark:border-zinc-600 placeholder-gray-400 dark:placeholder-gray-500"
      placeholder="Remplacement"
      bind:value={newReplacement}
    />
    <label class="regex-label text-sm text-zinc-600 dark:text-zinc-300 select-none">
      <input type="checkbox" bind:checked={isRegex} class="mr-1 accent-blue-600 dark:accent-blue-400" />
      Regex ?
    </label>
    <button class="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm" on:click={addRule}>Ajouter</button>
  </div>

  {#if $customReplacementRules.length > 0}
    {#each $customReplacementRules as rule, index}
      <div class="rule-entry">
        <input type="text" class="border p-1 rounded bg-gray-100 dark:bg-zinc-700 dark:border-zinc-600 text-zinc-800 dark:text-zinc-100" value={rule.pattern} readonly />
        <span class="text-zinc-700 dark:text-zinc-300">→</span>
        <input type="text" class="border p-1 rounded bg-gray-100 dark:bg-zinc-700 dark:border-zinc-600 text-zinc-800 dark:text-zinc-100" value={rule.replacement} readonly />
        <span class="text-sm italic text-gray-500 dark:text-gray-400">{rule.isRegex ? '(Regex)' : '(Texte exact)'}</span>
        <button
          type="button"
          class="delete-btn ml-auto sm:ml-2" on:click={() => removeRule(index)}
          title="Supprimer la règle"
        >
          🗑️ </button>
      </div>
    {/each}
  {:else}
    <p class="text-gray-500 dark:text-gray-400 italic text-sm">Aucune règle définie.</p>
  {/if}
</div>