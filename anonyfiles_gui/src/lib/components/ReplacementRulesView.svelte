<!-- #anonyfiles/anonyfiles_gui/src/lib/components/ReplacementRulesView.svelte -->
<script lang="ts">
  import { customReplacementRules } from '$lib/stores/customReplacementRules';
  import { get } from 'svelte/store';
  import { Puzzle, Download, ArrowRight, Check, X } from 'lucide-svelte';
  import WordlistRuleGenerator from './WordlistRuleGenerator.svelte';

  let rules = get(customReplacementRules);

  const unsubscribe = customReplacementRules.subscribe((value) => {
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

<div class="w-full max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 pb-10">
  <div class="mb-5 flex items-center gap-3">
    <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 dark:bg-brand-900/30 text-brand-600 dark:text-brand-100">
      <Puzzle size={20} />
    </div>
    <div>
      <h1 class="text-lg font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
        Règles de remplacement avancées
      </h1>
      <p class="text-xs text-zinc-500 dark:text-zinc-400">
        Vue d'ensemble des règles actuellement actives, avec export JSON.
      </p>
    </div>
  </div>

  <section class="ui-section mb-5">
    <header class="ui-section-header justify-between">
      <span class="ui-section-title">Règles actives</span>
      {#if rules.length > 0}
        <span class="ui-badge-brand">{rules.length}</span>
      {/if}
    </header>
    <div class="ui-section-body">
      {#if rules.length === 0}
        <p class="text-sm text-zinc-500 dark:text-zinc-400 italic">
          Aucune règle définie. Ajoute-les via l'onglet Anonymisation ou le générateur ci-dessous.
        </p>
      {:else}
        <ul class="divide-y divide-zinc-200 dark:divide-zinc-700 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50/50 dark:bg-zinc-900/40">
          {#each rules as rule}
            <li class="flex flex-wrap items-center gap-3 px-4 py-2.5">
              <code class="flex-1 min-w-0 truncate text-xs font-mono bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-md px-2 py-1 text-zinc-800 dark:text-zinc-100" title={rule.pattern}>
                {rule.pattern}
              </code>
              <ArrowRight size={14} class="text-zinc-400 shrink-0" />
              <code class="flex-1 min-w-0 truncate text-xs font-mono bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-md px-2 py-1 text-zinc-800 dark:text-zinc-100" title={rule.replacement}>
                {rule.replacement}
              </code>
              <span class="ui-badge shrink-0 inline-flex items-center gap-1">
                {#if rule.isRegex}
                  <Check size={12} class="text-emerald-500" />
                  Regex
                {:else}
                  <X size={12} class="text-zinc-400" />
                  Texte
                {/if}
              </span>
            </li>
          {/each}
        </ul>

        <div class="mt-3 flex justify-end">
          <button type="button" class="ui-btn-secondary" on:click={exportAsJSON}>
            <Download size={16} />
            Exporter en JSON
          </button>
        </div>
      {/if}
    </div>
  </section>

  <section class="ui-section">
    <header class="ui-section-header">
      <span class="ui-section-title">Générateur à partir d'une wordlist</span>
    </header>
    <div class="ui-section-body">
      <WordlistRuleGenerator />
    </div>
  </section>
</div>
