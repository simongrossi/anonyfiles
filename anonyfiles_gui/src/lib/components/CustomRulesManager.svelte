<script lang="ts">
  import { customReplacementRules } from '../stores/customRulesStore';
  import { Wrench, Plus, Trash2, Regex, ArrowRight } from 'lucide-svelte';

  let newPattern = '';
  let newReplacement = '';
  let isRegex = false;

  function addRule() {
    if (!newPattern.trim()) return;
    customReplacementRules.update((rules) => [
      ...rules,
      {
        pattern: newPattern.trim(),
        replacement: newReplacement.trim(),
        isRegex,
      },
    ]);
    newPattern = '';
    newReplacement = '';
    isRegex = false;
  }

  function removeRule(index: number) {
    customReplacementRules.update((rules) => rules.filter((_, i) => i !== index));
  }

  function toggleRegex() {
    isRegex = !isRegex;
  }

  function handleKey(event: KeyboardEvent) {
    if (event.key === 'Enter') {
      event.preventDefault();
      addRule();
    }
  }
</script>

<section class="ui-section mb-5">
  <header class="ui-section-header justify-between">
    <div class="flex items-center gap-2">
      <Wrench size={16} class="text-zinc-400 dark:text-zinc-500" />
      <span class="ui-section-title">Règles de remplacement personnalisées</span>
    </div>
    {#if $customReplacementRules.length > 0}
      <span class="ui-badge-brand">{$customReplacementRules.length}</span>
    {/if}
  </header>

  <div class="ui-section-body space-y-4">
    <div class="grid grid-cols-1 sm:grid-cols-[1fr_auto_1fr_auto] gap-3 items-end">
      <div>
        <label for="custom-rule-pattern" class="ui-field-label">Motif à remplacer</label>
        <input
          id="custom-rule-pattern"
          type="text"
          class="ui-input"
          placeholder={isRegex ? '\\b\\d{10}\\b' : 'Confidentiel'}
          bind:value={newPattern}
          on:keydown={handleKey}
        />
      </div>
      <div class="hidden sm:flex items-center justify-center pb-2 text-zinc-400">
        <ArrowRight size={16} />
      </div>
      <div>
        <label for="custom-rule-replacement" class="ui-field-label">Remplacement</label>
        <input
          id="custom-rule-replacement"
          type="text"
          class="ui-input"
          placeholder="[SECRET]"
          bind:value={newReplacement}
          on:keydown={handleKey}
        />
      </div>
      <div class="flex items-center gap-2">
        <button
          type="button"
          class="ui-chip {isRegex ? 'ui-chip-on' : 'ui-chip-off'}"
          on:click={toggleRegex}
          title="Activer/désactiver le mode Regex"
          aria-pressed={isRegex}
        >
          <Regex size={14} strokeWidth={2} />
          Regex
        </button>
        <button
          type="button"
          class="ui-btn-primary"
          on:click={addRule}
          disabled={!newPattern.trim()}
        >
          <Plus size={16} />
          Ajouter
        </button>
      </div>
    </div>

    {#if $customReplacementRules.length > 0}
      <ul class="divide-y divide-zinc-200 dark:divide-zinc-700 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50/50 dark:bg-zinc-900/40">
        {#each $customReplacementRules as rule, index}
          <li class="flex items-center gap-3 px-4 py-2.5">
            <code class="flex-1 truncate text-xs text-zinc-800 dark:text-zinc-100 font-mono bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-md px-2 py-1" title={rule.pattern}>
              {rule.pattern}
            </code>
            <ArrowRight size={14} class="text-zinc-400 shrink-0" />
            <code class="flex-1 truncate text-xs text-zinc-800 dark:text-zinc-100 font-mono bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-md px-2 py-1" title={rule.replacement || '(vide)'}>
              {rule.replacement || '∅'}
            </code>
            <span class="ui-badge {rule.isRegex ? 'ui-badge-brand' : ''} shrink-0">
              {rule.isRegex ? 'Regex' : 'Texte'}
            </span>
            <button
              type="button"
              class="ui-icon-btn hover:!text-red-600 hover:!bg-red-50 dark:hover:!bg-red-900/30"
              on:click={() => removeRule(index)}
              title="Supprimer la règle"
              aria-label="Supprimer la règle"
            >
              <Trash2 size={16} />
            </button>
          </li>
        {/each}
      </ul>
    {:else}
      <p class="text-sm text-zinc-500 dark:text-zinc-400 italic">
        Aucune règle définie. Les entrées ci-dessus créent une règle texte exact ou regex.
      </p>
    {/if}
  </div>
</section>
