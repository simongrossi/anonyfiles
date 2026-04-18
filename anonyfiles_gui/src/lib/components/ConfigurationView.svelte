<!-- #anonyfiles/anonyfiles_gui/src/lib/components/ConfigurationView.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { Settings2, Palette, Save, Sun, Moon, Monitor } from 'lucide-svelte';
  import ConfigPresetManager from './ConfigPresetManager.svelte';

  type ThemeMode = 'auto' | 'light' | 'dark';

  function getStoredThemeMode(): ThemeMode {
    if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
      const val = localStorage.getItem('theme');
      if (val === 'light' || val === 'dark' || val === 'auto') return val;
    }
    return 'auto';
  }

  let themeMode: ThemeMode = getStoredThemeMode();

  function applyTheme(modeToApply: ThemeMode) {
    if (typeof window === 'undefined') return;

    const root = document.documentElement;
    let applyDark = false;

    if (modeToApply === 'dark') applyDark = true;
    else if (modeToApply === 'light') applyDark = false;
    else applyDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (applyDark) root.classList.add('dark');
    else root.classList.remove('dark');
  }

  function handleThemeChange(newMode: ThemeMode) {
    themeMode = newMode;
    if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
      localStorage.setItem('theme', newMode);
    }
  }

  let mediaQueryList: MediaQueryList | null = null;

  function handleSystemThemeChange() {
    if (themeMode === 'auto') applyTheme('auto');
  }

  function setupSystemThemeListener() {
    if (typeof window === 'undefined') return;

    if (mediaQueryList) {
      mediaQueryList.removeEventListener('change', handleSystemThemeChange);
      mediaQueryList = null;
    }

    if (themeMode === 'auto') {
      mediaQueryList = window.matchMedia('(prefers-color-scheme: dark)');
      mediaQueryList.addEventListener('change', handleSystemThemeChange);
    }
  }

  onMount(() => {
    applyTheme(themeMode);
    setupSystemThemeListener();

    return () => {
      if (mediaQueryList) {
        mediaQueryList.removeEventListener('change', handleSystemThemeChange);
      }
    };
  });

  $: {
    if (typeof window !== 'undefined') {
      applyTheme(themeMode);
      setupSystemThemeListener();
    }
  }

  const themeOptions: Array<{ id: ThemeMode; label: string; icon: typeof Sun }> = [
    { id: 'light', label: 'Clair', icon: Sun },
    { id: 'dark', label: 'Sombre', icon: Moon },
    { id: 'auto', label: 'Auto', icon: Monitor },
  ];
</script>

<div class="w-full max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 pb-10">
  <div class="mb-5 flex items-center gap-3">
    <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 dark:bg-brand-900/30 text-brand-600 dark:text-brand-100">
      <Settings2 size={20} />
    </div>
    <div>
      <h1 class="text-lg font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
        Configuration
      </h1>
      <p class="text-xs text-zinc-500 dark:text-zinc-400">
        Préférences d'interface et gestion des presets.
      </p>
    </div>
  </div>

  <!-- Thème -->
  <section class="ui-section mb-5">
    <header class="ui-section-header">
      <Palette size={16} class="text-zinc-400 dark:text-zinc-500" />
      <span class="ui-section-title">Apparence</span>
    </header>
    <div class="ui-section-body">
      <span id="theme-label" class="ui-field-label">Thème</span>
      <div
        class="inline-flex p-1 rounded-xl bg-zinc-100 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-700"
        role="radiogroup"
        aria-labelledby="theme-label"
      >
        {#each themeOptions as opt}
          {@const Icon = opt.icon}
          {@const active = themeMode === opt.id}
          <button
            type="button"
            role="radio"
            aria-checked={active}
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition
                   {active
                     ? 'bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 shadow-sm'
                     : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-zinc-200'}"
            on:click={() => handleThemeChange(opt.id)}
          >
            <Icon size={14} />
            {opt.label}
          </button>
        {/each}
      </div>
    </div>
  </section>

  <!-- Presets -->
  <section class="ui-section">
    <header class="ui-section-header">
      <Save size={16} class="text-zinc-400 dark:text-zinc-500" />
      <span class="ui-section-title">Presets de configuration</span>
    </header>
    <div class="ui-section-body">
      <ConfigPresetManager />
    </div>
  </section>
</div>
