<!-- #anonyfiles/anonyfiles_gui/src/lib/components/AnonymizationOptions.svelte -->
<script lang="ts">
  export let options: Array<{ key: string, label: string, default: boolean }>;
  export let selected: { [key: string]: boolean };
  export let isLoading: boolean = false;

  function toggle(key: string) {
    selected[key] = !selected[key];
  }
</script>

<div class="flex flex-wrap gap-3 mb-3 mt-1">
  {#each options as opt}
    <button
      type="button"
      on:click={() => toggle(opt.key)}
      disabled={isLoading}
      class={`group px-3 py-1.5 text-sm rounded-full font-medium border transition-all duration-200 ease-in-out 
              transform hover:scale-105 active:scale-95 select-none flex items-center gap-1
              focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2
              ${
                selected[opt.key]
                  ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                  : 'bg-white text-zinc-800 dark:bg-zinc-800 dark:text-zinc-100 border-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-700'
              }`}
    >
      {#if selected[opt.key]}
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 00-1.414 0L9 11.586 5.707 8.293a1 1 0 00-1.414 1.414l4 4a1 1 0 001.414 0l7-7a1 1 0 000-1.414z" clip-rule="evenodd" />
        </svg>
      {/if}
      {opt.label}
    </button>
  {/each}
</div>
