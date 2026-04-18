<script lang="ts">
  import { customReplacementRules } from '../stores/customRulesStore';

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

  function toggleRegex() {
    isRegex = !isRegex;
  }
</script>

<style>
  /* Vos styles existants pour les règles personnalisées */
  .rule-entry {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 0.5rem;
  }
  :global(html.dark) .rule-entry {
    border-bottom-color: #374151;
  }

  .rule-entry input[type="text"] {
    flex: 1 1 150px;
  }

  .regex-toggle-button {
    background-color: #e5e7eb;
    color: #4b5563;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.875rem;
    cursor: pointer;
    transition: background-color 0.2s, color 0.2s;
    border: 1px solid transparent;
  }

  .regex-toggle-button.active {
    background-color: #3b82f6;
    color: white;
    border-color: #2563eb;
  }

  :global(html.dark) .regex-toggle-button {
    background-color: #4b5563;
    color: #d1d5db;
    border-color: #374151;
  }

  :global(html.dark) .regex-toggle-button.active {
    background-color: #60a5fa;
    color: white;
    border-color: #3b82f6;
  }

  .rule-form {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1rem;
    align-items: center;
  }

  .section-title {
    font-weight: bold;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
    font-size: 1.1rem;
  }

  .delete-btn {
    color: #ef4444;
    font-weight: bold;
    cursor: pointer;
    background: none;
    border: none;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
  }

  .delete-btn:hover {
    background-color: #fee2e2;
  }
  :global(html.dark) .delete-btn:hover {
    background-color: #3f2121;
    color: #fca5a5;
  }
  :global(html.dark) .delete-btn {
    color: #f87171;
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
      class="border rounded p-1 text-zinc-800 bg-white dark:text-zinc-100 dark:bg-zinc-700 dark:border-zinc-600 placeholder-gray-400 dark:placeholder-500"
      placeholder="Remplacement"
      bind:value={newReplacement}
    />
    <button
      class="regex-toggle-button"
      class:active={isRegex}
      on:click={toggleRegex}
      title="Activer/Désactiver le mode Regex"
    >
      Regex
    </button>
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
          🗑️
        </button>
      </div>
    {/each}
  {:else}
    <p class="text-gray-500 dark:text-gray-400 italic text-sm">Aucune règle définie.</p>
  {/if}
</div>