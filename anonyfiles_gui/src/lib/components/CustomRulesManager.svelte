<script lang="ts">
  import { customReplacementRules } from '../stores/customRulesStore';
  import { get } from 'svelte/store';

  let newPattern = '';
  let newReplacement = '';
  let isRegex = false; // Initialisé à false, pas de regex par défaut

  function addRule() {
    if (!newPattern.trim()) return;
    customReplacementRules.update(rules => [
      ...rules,
      {
        pattern: newPattern.trim(),
        replacement: newReplacement.trim(),
        isRegex // Utilise la valeur de isRegex
      }
    ]);
    newPattern = '';
    newReplacement = '';
    isRegex = false; // Réinitialise à false après ajout
  }

  function removeRule(index: number) {
    customReplacementRules.update(rules =>
      rules.filter((_, i) => i !== index)
    );
  }

  // Fonction pour basculer l'état de isRegex
  function toggleRegex() {
    isRegex = !isRegex;
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
  :global(html.dark) .rule-entry {
    /* Séparateur en mode sombre */
    border-bottom-color: #374151; /* Tailwind gray-700 */
  }

  .rule-entry input[type="text"] {
    flex: 1 1 150px; /* Base plus petite, permet de mieux s'adapter */
  }

  .regex-toggle-button {
    /* Styles de base pour le bouton toggle */
    background-color: #e5e7eb; /* gray-200 */
    color: #4b5563; /* gray-700 */
    padding: 0.25rem 0.75rem;
    border-radius: 9999px; /* fully rounded */
    font-size: 0.875rem; /* text-sm */
    cursor: pointer;
    transition: background-color 0.2s, color 0.2s;
    border: 1px solid transparent;
  }

  .regex-toggle-button.active {
    background-color: #3b82f6; /* blue-500 */
    color: white;
    border-color: #2563eb; /* blue-600 */
  }

  /* Dark mode styles for the toggle button */
  :global(html.dark) .regex-toggle-button {
    background-color: #4b5563; /* gray-700 */
    color: #d1d5db; /* gray-300 */
    border-color: #374151; /* gray-800 */
  }

  :global(html.dark) .regex-toggle-button.active {
    background-color: #60a5fa; /* blue-400 */
    color: white;
    border-color: #3b82f6; /* blue-500 */
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