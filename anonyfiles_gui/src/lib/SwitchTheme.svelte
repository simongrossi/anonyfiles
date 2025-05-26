<script lang="ts">
  export let mode: 'auto' | 'light' | 'dark' = 'auto';
  export let onChange: (mode: 'auto' | 'light' | 'dark') => void;
</script>

<div class="flex gap-3">
  <button
    class="px-4 py-2 rounded-xl font-semibold border transition
      focus:outline-none focus:ring-2 focus:ring-primary flex items-center gap-2
      border-gray-300 dark:border-gray-700"
    class:bg-primary={mode === 'auto' && !document.body.classList.contains('dark')}
    class:text-white={mode === 'auto'}
    class:bg-accent={mode === 'auto' && document.body.classList.contains('dark')}
    class:text-gray-900={mode === 'auto' && document.body.classList.contains('dark')}
    aria-pressed={mode === 'auto'}
    on:click={() => onChange('auto')}
    type="button"
  >🖥️ Auto</button>

  <button
    class="px-4 py-2 rounded-xl font-semibold border transition
      focus:outline-none focus:ring-2 focus:ring-primary flex items-center gap-2
      border-gray-300 dark:border-gray-700"
    class:bg-primary={mode === 'light' && !document.body.classList.contains('dark')}
    class:text-white={mode === 'light'}
    class:bg-accent={mode === 'light' && document.body.classList.contains('dark')}
    class:text-gray-900={mode === 'light' && document.body.classList.contains('dark')}
    aria-pressed={mode === 'light'}
    on:click={() => onChange('light')}
    type="button"
  >🌞 Clair</button>

  <button
    class="px-4 py-2 rounded-xl font-semibold border transition
      focus:outline-none focus:ring-2 focus:ring-primary flex items-center gap-2
      border-gray-300 dark:border-gray-700"
    class:bg-primary={mode === 'dark' && !document.body.classList.contains('dark')}
    class:text-white={mode === 'dark'}
    class:bg-accent={mode === 'dark' && document.body.classList.contains('dark')}
    class:text-gray-900={mode === 'dark' && document.body.classList.contains('dark')}
    aria-pressed={mode === 'dark'}
    on:click={() => onChange('dark')}
    type="button"
  >🌙 Sombre</button>
</div>
