<script lang="ts">
  import { createEventDispatcher } from "svelte";
  export let accept: string = "";
  export let multiple: boolean = false;

  const dispatch = createEventDispatcher();

  let isDragging = false;

  function handleDragOver(event: DragEvent) {
    event.preventDefault();
    isDragging = true;
  }

  function handleDragLeave(event: DragEvent) {
    event.preventDefault();
    isDragging = false;
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault();
    isDragging = false;
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      dispatch("drop", { files });
    }
  }

  function handleClick() {
    fileInput.click();
  }

  let fileInput: HTMLInputElement;
  function handleFileChange(event: Event) {
    const files = (event.target as HTMLInputElement).files;
    if (files && files.length > 0) {
      dispatch("drop", { files });
    }
  }
</script>

<div
  class="border-2 border-dashed rounded-xl border-zinc-500 transition-all bg-zinc-950 text-zinc-100 text-center px-4 py-6 mb-5 cursor-pointer select-none relative
         hover:border-blue-400 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
  class:ring-4={isDragging}
  class:ring-blue-400={isDragging}
  tabindex="0"
  role="region"
  aria-label="Zone de dépôt de fichiers"
  on:dragover={handleDragOver}
  on:dragleave={handleDragLeave}
  on:drop={handleDrop}
  on:click={handleClick}
  on:keydown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  }}
>
  <slot>
    <span class="text-zinc-200">Déposez vos fichiers ici ou cliquez pour sélectionner.</span>
    {#if isDragging}
      <div class="absolute inset-0 flex items-center justify-center pointer-events-none animate-pulse">
        <svg class="h-12 w-12 text-blue-300 opacity-70" fill="none" stroke="currentColor" stroke-width="2"
          viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round"
            d="M7 16V8a4 4 0 014-4h2a4 4 0 014 4v8m1 0a2 2 0 002-2V8a6 6 0 00-6-6H9a6 6 0 00-6 6v6a2 2 0 002 2h12z" />
        </svg>
      </div>
    {/if}
  </slot>
  <input
    type="file"
    bind:this={fileInput}
    {accept}
    {multiple}
    class="hidden"
    on:change={handleFileChange}
  />
</div>
