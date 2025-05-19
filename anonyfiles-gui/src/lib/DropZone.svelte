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
  class="transition-colors duration-200 border-2 border-dashed rounded-xl text-center cursor-pointer select-none px-4 py-8 bg-slate-100 text-slate-700
    focus:outline-none focus:ring-2 focus:ring-blue-400
    hover:border-blue-400
    {isDragging ? 'bg-blue-50 border-blue-500 text-blue-700' : ''}"
  role="region"
  aria-label="Zone de dépôt de fichiers"
  tabindex="0"
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
    <p class="text-base m-0">Déposez vos fichiers ici ou cliquez pour sélectionner.</p>
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
