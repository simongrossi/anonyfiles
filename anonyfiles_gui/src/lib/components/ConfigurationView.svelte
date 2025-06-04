<!-- #anonyfiles/anonyfiles_gui/src/lib/components/ConfigurationView.svelte -->
<script lang="ts">
  import SwitchTheme from './SwitchTheme.svelte';
  import { onMount, onDestroy } from 'svelte';
  import PresetSelector from './PresetSelector.svelte';

  function getStoredThemeMode(): 'auto' | 'light' | 'dark' {
    if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
      const val = localStorage.getItem('theme');
      if (val === 'light' || val === 'dark' || val === 'auto') return val;
    }
    return 'auto';
  }

  let themeMode: 'auto' | 'light' | 'dark' = getStoredThemeMode();

  function applyTheme(modeToApply: 'auto' | 'light' | 'dark') {
    if (typeof window === 'undefined') return;

    const root = document.documentElement;
    let applyDark = false;

    if (modeToApply === 'dark') {
      applyDark = true;
    } else if (modeToApply === 'light') {
      applyDark = false;
    } else {
      applyDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    }

    if (applyDark) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }

  function handleThemeChange(newMode: 'auto' | 'light' | 'dark') {
    themeMode = newMode;
    if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
      localStorage.setItem('theme', newMode);
    }
  }

  let mediaQueryList: MediaQueryList | null = null;

  function handleSystemThemeChange(event: MediaQueryListEvent) {
    if (themeMode === 'auto') {
      applyTheme('auto');
    }
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
</script>

<div class="max-w-xl mx-auto p-6 sm:p-8 bg-white dark:bg-zinc-800 rounded-2xl shadow-xl flex flex-col items-center border border-gray-200 dark:border-gray-700">
  <h2 class="text-2xl font-montserrat mb-6 text-zinc-700 dark:text-zinc-100 text-center">
    Configuration de l’interface
  </h2>

  <div class="mb-6 w-full flex flex-col items-center">
    <span id="theme-label" class="block mb-2 font-semibold text-zinc-600 dark:text-zinc-300">Thème :</span>
    <SwitchTheme
      mode={themeMode}
      onChange={handleThemeChange}
      aria-labelledby="theme-label"
    />
  </div>

</div>
