<!-- #anonyfiles/anonyfiles_gui/src/lib/components/CustomRulesManager.svelte -->
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
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    border-bottom: 1px solid #ccc;
    padding-bottom: 0.5rem;
  }

  .rule-entry input[type="text"] {
    flex: 1 1 200px;
  }

  .regex-label {
    display: flex;
    align-items: center;
    gap: 0.25rem;
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
    color: red;
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
</style>

<div>
  <div class="section-title">🔧 Règles de remplacement personnalisées</div>

  <div class="rule-form">
    <input
      type="text"
      class="border rounded p-1"
      placeholder="Motif à remplacer"
      bind:value={newPattern}
    />
    <input
      type="text"
      class="border rounded p-1"
      placeholder="Remplacement"
      bind:value={newReplacement}
    />
    <label class="regex-label">
      <input type="checkbox" bind:checked={isRegex} />
      Regex ?
    </label>
    <button class="bg-green-500 text-white px-3 py-1 rounded" on:click={addRule}>Ajouter</button>
  </div>

  {#if $customReplacementRules.length > 0}
    {#each $customReplacementRules as rule, index}
      <div class="rule-entry">
        <input type="text" class="border p-1 rounded" value={rule.pattern} readonly />
        <span>→</span>
        <input type="text" class="border p-1 rounded" value={rule.replacement} readonly />
        <span class="text-sm italic">{rule.isRegex ? 'Regex' : 'Texte exact'}</span>
        <button
          type="button"
          class="delete-btn"
          on:click={() => removeRule(index)}
        >
          🗑 Supprimer
        </button>
      </div>
    {/each}
  {:else}
    <p class="text-gray-500 italic">Aucune règle définie.</p>
  {/if}
</div>
