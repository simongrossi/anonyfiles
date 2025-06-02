<!-- #anonyfiles/anonyfiles_gui/src/routes/layout.svelte -->
<script lang="ts">
  import Header from '$lib/components/Header.svelte';
</script>

<Header title="Anonyfiles" />

<main class="pt-14 px-4 bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100 min-h-screen">
  <slot />
</main>
