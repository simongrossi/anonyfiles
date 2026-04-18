<!-- #anonyfiles/anonyfiles_gui/src/lib/components/AnonymizationOptions.svelte -->
<script lang="ts">
  import { Check, User, MapPin, AtSign, Landmark, Tag } from 'lucide-svelte';

  type Option = { key: string; label: string; default: boolean };

  export let options: Array<Option>;
  export let selected: { [key: string]: boolean };
  export let isLoading: boolean = false;

  // Regroupement sémantique des entités — purement cosmétique, ne change rien
  // au contrat du composant (options/selected).
  type Category = {
    id: string;
    label: string;
    icon: typeof User;
    keys: string[];
  };
  const categories: Category[] = [
    { id: 'identity', label: 'Identité', icon: User, keys: ['anonymizePersons', 'anonymizeOrgs'] },
    { id: 'places', label: 'Lieux & adresses', icon: MapPin, keys: ['anonymizeLocations', 'anonymizeAddresses'] },
    { id: 'contact', label: 'Contact', icon: AtSign, keys: ['anonymizeEmails', 'anonymizePhones'] },
    { id: 'finance', label: 'Finance & dates', icon: Landmark, keys: ['anonymizeIbans', 'anonymizeDates'] },
    { id: 'misc', label: 'Divers', icon: Tag, keys: ['anonymizeMisc'] },
  ];

  $: optionsByKey = Object.fromEntries(options.map((o) => [o.key, o]));
  $: activeCount = options.filter((o) => selected[o.key]).length;

  function toggle(key: string) {
    selected[key] = !selected[key];
  }

  function enableAll() {
    options.forEach((o) => (selected[o.key] = true));
    selected = selected;
  }
  function disableAll() {
    options.forEach((o) => (selected[o.key] = false));
    selected = selected;
  }
</script>

<section class="ui-section mb-5">
  <header class="ui-section-header justify-between">
    <div class="flex flex-col">
      <span class="ui-section-title">Entités à anonymiser</span>
      <span class="ui-section-subtitle">
        {activeCount} sélectionnée{activeCount > 1 ? 's' : ''} sur {options.length}
      </span>
    </div>
    <div class="flex items-center gap-1">
      <button
        type="button"
        class="ui-btn-ghost text-xs px-2 py-1"
        on:click={enableAll}
        disabled={isLoading || activeCount === options.length}
      >
        Tout activer
      </button>
      <button
        type="button"
        class="ui-btn-ghost text-xs px-2 py-1"
        on:click={disableAll}
        disabled={isLoading || activeCount === 0}
      >
        Tout désactiver
      </button>
    </div>
  </header>

  <div class="ui-section-body space-y-4">
    {#each categories as cat}
      {@const keys = cat.keys.filter((k) => optionsByKey[k])}
      {#if keys.length > 0}
        <div>
          <div class="flex items-center gap-2 mb-2">
            <svelte:component this={cat.icon} size={14} class="text-zinc-400 dark:text-zinc-500" />
            <span class="ui-chip-group-label">{cat.label}</span>
          </div>
          <div class="flex flex-wrap gap-2">
            {#each keys as key}
              {@const opt = optionsByKey[key]}
              {@const on = !!selected[key]}
              <button
                type="button"
                class="ui-chip {on ? 'ui-chip-on' : 'ui-chip-off'}"
                aria-pressed={on}
                on:click={() => toggle(key)}
                disabled={isLoading}
              >
                {#if on}
                  <Check size={12} strokeWidth={2.5} />
                {/if}
                {opt.label}
              </button>
            {/each}
          </div>
        </div>
      {/if}
    {/each}
  </div>
</section>
