<script lang="ts">
  import SwitchTheme from './SwitchTheme.svelte';

  function getThemeMode(): 'auto' | 'light' | 'dark' {
    const val = localStorage.getItem('theme');
    if (val === 'light' || val === 'dark' || val === 'auto') return val;
    return 'auto';
  }

  let themeMode: 'auto' | 'light' | 'dark' = getThemeMode();

  function applyTheme(mode: 'auto' | 'light' | 'dark') {
    if (mode === 'dark') {
      document.body.classList.add('dark');
    } else if (mode === 'light') {
      document.body.classList.remove('dark');
    } else if (mode === 'auto') {
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.body.classList.add('dark');
      } else {
        document.body.classList.remove('dark');
      }
    }
  }

  applyTheme(themeMode);

  function handleThemeChange(mode: 'auto' | 'light' | 'dark') {
    themeMode = mode;
    localStorage.setItem('theme', mode);
    applyTheme(mode);
  }

  let mq: MediaQueryList | null = null;
  function listenToSystemTheme() {
    if (mq) mq.removeEventListener('change', onSystemThemeChange);
    if (themeMode === 'auto') {
      mq = window.matchMedia('(prefers-color-scheme: dark)');
      mq.addEventListener('change', onSystemThemeChange);
    }
  }
  function onSystemThemeChange() {
    if (themeMode === 'auto') {
      applyTheme('auto');
    }
  }
  listenToSystemTheme();
  $: {
    listenToSystemTheme();
    applyTheme(themeMode);
  }
</script>

<div class="max-w-xl mx-auto p-8 bg-white dark:bg-gray-900 rounded-2xl shadow-xl flex flex-col items-center">
  <h2 class="text-2xl font-montserrat mb-6 text-primary dark:text-accent">
    Configuration de l’interface
  </h2>

  <div class="mb-6">
    <span id="theme-label" class="block mb-2 font-semibold">Thème :</span>
    <SwitchTheme
      mode={themeMode}
      onChange={handleThemeChange}
      aria-labelledby="theme-label"
    />
  </div>
  <!-- Ajoute ici d’autres options de configuration -->
</div>
