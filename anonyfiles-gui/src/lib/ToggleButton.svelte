<script lang="ts">
  export let checked: boolean;
  export let onToggle: () => void;
</script>

<button
  class="flex items-center px-4 py-2 bg-gray-200 dark:bg-gray-700 rounded-xl transition shadow focus:outline-none focus:ring-2 focus:ring-primary select-none"
  on:click={onToggle}
  aria-pressed={checked}
  type="button"
>
  <span class="mr-3">{checked ? '🌙 Mode sombre' : '☀️ Mode clair'}</span>
  <span
    class="w-10 h-6 flex items-center bg-gray-400 dark:bg-gray-600 rounded-full p-1 transition"
  >
    <span
      class="w-4 h-4 bg-white rounded-full shadow transform transition"
      class:translate-x-4={checked}
    ></span>
  </span>
</button>
