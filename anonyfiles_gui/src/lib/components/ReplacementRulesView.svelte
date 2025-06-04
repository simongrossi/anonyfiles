<!-- #anonyfiles/anonyfiles_gui/src/lib/components/ReplacementRulesView.svelte -->
<script lang="ts">
  import { customReplacementRules } from '$lib/stores/customReplacementRules';
  import { get } from 'svelte/store';
  import WordlistRuleGenerator from './WordlistRuleGenerator.svelte';

  let rules = get(customReplacementRules);

  const unsubscribe = customReplacementRules.subscribe(value => {
    rules = value;
  });

  function exportAsJSON() {
    const json = JSON.stringify(rules, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = 'anonyfiles_rules.json';
    a.click();
    URL.revokeObjectURL(url);
  }
</script>

<div class="p-6 space-y-10">
  <div>
    <h1 class="text-2xl font-bold">🧩 Règles de remplacement avancées</h1>
    <p class="text-gray-600">Voici les règles personnalisées actuellement actives :</p>

    {#if rules.length === 0}
      <p class="text-yellow-600 mt-2">Aucune règle définie.</p>
    {:else}
      <ul class="space-y-2 mt-4">
        {#each rules as rule, index}
          <li class="border border-gray-300 rounded-lg p-3 bg-white shadow-sm">
            <p><strong>Motif :</strong> <code>{rule.pattern}</code></p>
            <p><strong>Remplacement :</strong> <code>{rule.replacement}</code></p>
            <p><strong>Regex :</strong> {rule.isRegex ? '✅' : '❌'}</p>
          </li>
        {/each}
      </ul>
    {/if}

    <button
      on:click={exportAsJSON}
      class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 mt-4"
    >
      ⬇️ Exporter en JSON
    </button>
  </div>

  <div class="border-t pt-6">
    <WordlistRuleGenerator />
  </div>
</div>

<style>
  code {
    background-color: #f3f3f3;
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
  }
</style>
