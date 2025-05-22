<script lang="ts">
  export let options: Array<{ key: string, label: string, default: boolean }>;
  export let selected: { [key: string]: boolean };
  export let isLoading: boolean = false;
</script>

<div class="flex flex-wrap gap-5 mb-3 mt-1">
    {#each options as opt}
        <div class="flex items-center gap-2">
            <input
                type="checkbox"
                id={opt.key}
                bind:checked={selected[opt.key]}
                class="w-5 h-5 accent-blue-600 border-zinc-400 focus:ring-blue-400 bg-zinc-200 rounded dark:accent-blue-400 dark:bg-gray-700 dark:border-gray-500"
                disabled={isLoading}
            />
            <label for={opt.key} class="select-none text-zinc-800 text-base font-medium dark:text-zinc-100">
                {opt.label}
            </label>
        </div>
    {/each}
</div>
