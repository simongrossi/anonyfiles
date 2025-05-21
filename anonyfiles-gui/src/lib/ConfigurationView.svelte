<script lang="ts">
  import SwitchTheme from './SwitchTheme.svelte';

  // Lit la préférence depuis localStorage
  function getThemeMode(): 'auto' | 'light' | 'dark' {
    const val = localStorage.getItem('theme');
    if (val === 'light' || val === 'dark' || val === 'auto') return val;
    return 'auto';
  }

  let themeMode: 'auto' | 'light' | 'dark' = getThemeMode();

  // Applique le thème à l'interface
  function applyTheme(mode: 'auto' | 'light' | 'dark') {
    if (mode === 'dark') {
      document.body.classList.add('dark');
    } else if (mode === 'light') {
      document.body.classList.remove('dark');
    } else if (mode === 'auto') {
      // Suivre la préférence système
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.body.classList.add('dark');
      } else {
        document.body.classList.remove('dark');
      }
    }
  }

  // Applique dès le chargement
  applyTheme(themeMode);

  // Gère le changement du mode thème
  function handleThemeChange(mode: 'auto' | 'light' | 'dark') {
    themeMode = mode;
    localStorage.setItem('theme', mode);
    applyTheme(mode);
  }

  // Écoute le changement de préférence système si "auto"
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

  // Sur changement du mode via UI
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
    <label class="block mb-2 font-semibold">Thème :</label>
    <SwitchTheme mode={themeMode} onChange={handleThemeChange} />
  </div>
  <!-- Ajoute ici d’autres options de configuration -->
</div>
