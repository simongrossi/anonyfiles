<!-- #anonyfiles/anonyfiles_gui/src/lib/components/AnonymizationOptions.svelte -->
<script lang="ts">
  import {
    Briefcase,
    Check,
    FileText,
    Landmark,
    MapPin,
    ShieldCheck,
    SlidersHorizontal,
    Tag,
    Terminal,
    User,
    AtSign,
  } from 'lucide-svelte';
  import {
    ANONYMIZATION_PROFILES,
    findMatchingAnonymizationProfile,
    selectionFromProfile,
    type AnonymizationOption,
    type AnonymizationOptionKey,
    type AnonymizationProfile,
    type AnonymizationSelection,
  } from '$lib/data/anonymizationProfiles';

  let {
    options,
    selected = $bindable(),
    isLoading = false,
  }: {
    options: Array<AnonymizationOption>;
    selected: AnonymizationSelection;
    isLoading?: boolean;
  } = $props();

  // Regroupement sémantique des entités — purement cosmétique, ne change rien
  // au contrat du composant (options/selected).
  type Category = {
    id: string;
    label: string;
    icon: typeof User;
    keys: AnonymizationOptionKey[];
  };
  const categories: Category[] = [
    { id: 'identity', label: 'Identité', icon: User, keys: ['anonymizePersons', 'anonymizeOrgs'] },
    { id: 'places', label: 'Lieux & adresses', icon: MapPin, keys: ['anonymizeLocations', 'anonymizeAddresses'] },
    { id: 'contact', label: 'Contact', icon: AtSign, keys: ['anonymizeEmails', 'anonymizePhones'] },
    { id: 'finance', label: 'Finance & dates', icon: Landmark, keys: ['anonymizeIbans', 'anonymizeDates'] },
    { id: 'misc', label: 'Divers', icon: Tag, keys: ['anonymizeMisc'] },
  ];

  const profileIcons: Record<string, typeof User> = {
    'strict-rgpd': ShieldCheck,
    leger: SlidersHorizontal,
    'documents-rh': Briefcase,
    contrats: FileText,
    'logs-techniques': Terminal,
  };

  const optionsByKey = $derived(Object.fromEntries(options.map((o) => [o.key, o])));
  const activeCount = $derived(options.filter((o) => selected[o.key]).length);
  const activeProfile = $derived(findMatchingAnonymizationProfile(selected));
  const activeProfileLabel = $derived(activeProfile?.label ?? 'Personnalisé');

  function commit(next: Partial<AnonymizationSelection>) {
    selected = { ...selected, ...next };
  }

  function toggle(key: AnonymizationOptionKey) {
    commit({ [key]: !selected[key] });
  }

  function enableAll() {
    commit(Object.fromEntries(options.map((o) => [o.key, true])) as Partial<AnonymizationSelection>);
  }
  function disableAll() {
    commit(Object.fromEntries(options.map((o) => [o.key, false])) as Partial<AnonymizationSelection>);
  }

  function applyProfile(profile: AnonymizationProfile) {
    selected = selectionFromProfile(profile);
  }

  function profileIcon(profile: AnonymizationProfile) {
    return profileIcons[profile.id] ?? ShieldCheck;
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
    <div>
      <div class="flex items-center justify-between gap-3 mb-2">
        <div class="flex items-center gap-2">
          <ShieldCheck size={14} class="text-zinc-400 dark:text-zinc-500" />
          <span class="ui-chip-group-label">Profil</span>
        </div>
        <span class="ui-badge-brand">{activeProfileLabel}</span>
      </div>

      <div
        class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2"
        role="radiogroup"
        aria-label="Profils d'anonymisation"
      >
        {#each ANONYMIZATION_PROFILES as profile}
          {@const on = activeProfile?.id === profile.id}
          <button
            type="button"
            role="radio"
            aria-checked={on}
            class="min-h-13 rounded-lg border px-2 py-2 text-xs font-semibold transition flex flex-col items-center justify-center gap-1 text-center {on ? 'border-brand-600 bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-100' : 'border-zinc-200 bg-white text-zinc-600 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700'}"
            title={profile.description}
            on:click={() => applyProfile(profile)}
            disabled={isLoading}
          >
            <svelte:component this={profileIcon(profile)} size={15} strokeWidth={2.2} />
            <span class="leading-tight">{profile.label}</span>
          </button>
        {/each}
      </div>
    </div>

    <div class="h-px bg-zinc-100 dark:bg-zinc-700"></div>

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
