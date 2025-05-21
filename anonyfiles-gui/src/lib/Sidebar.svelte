<!-- Sidebar.svelte (exemple) -->
<nav class="flex flex-col p-4 bg-zinc-900 text-white h-full">
  <button class="mb-4" on:click={() => currentView = 'anonymizer'}>
    🛡️ Anonymiser
  </button>
  <button on:click={() => currentView = 'deanonymizer'}>
    🕵️‍♂️ Désanonymer
  </button>
</nav>
