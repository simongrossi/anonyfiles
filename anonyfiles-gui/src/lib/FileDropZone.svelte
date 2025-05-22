<script lang="ts">
  import { createEventDispatcher } from "svelte";
  export let fileName: string = "";
  export let dragActive: boolean = false;

  const dispatch = createEventDispatcher();

  function handleDrop(event: DragEvent) {
    event.preventDefault();
    const file = event.dataTransfer?.files?.[0];
    if (file) {
      dispatch("file", { file });
    }
  }
  function handleDragOver(event: DragEvent) {
    event.preventDefault();
    dispatch("dragover");
  }
  function handleDragLeave(event: DragEvent) {
    event.preventDefault();
    dispatch("dragleave");
  }
  function handleFileInput(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) {
      dispatch("file", { file });
    }
  }
</script>

<div
  role="region"
  class="w-full mb-6 border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center cursor-pointer transition bg-zinc-100 hover:bg-zinc-200 dark:bg-gray-700 dark:hover:bg-gray-600"
  class:bg-blue-50={dragActive}
  class:border-blue-500={dragActive}
  on:drop={handleDrop}
  on:dragover={handleDragOver}
  on:dragleave={handleDragLeave}
>
  <input
    type="file"
    id="fileInput"
    accept=".txt,.csv,.xlsx,.docx,.pdf,.json"
    class="hidden"
    on:change={handleFileInput}
  />
  <label for="fileInput" class="cursor-pointer flex flex-col items-center gap-2">
    <span class="text-base font-medium text-zinc-700 dark:text-zinc-200"
      >Déposez un fichier ou cliquez pour parcourir</span
    >
    <span class="text-sm text-zinc-500 dark:text-zinc-400"
      >Formats supportés : .txt, .csv, .xlsx, .docx, .pdf, .json</span
    >
    {#if fileName}
      <span class="text-blue-800 font-semibold mt-2 dark:text-blue-400">{fileName}</span>
    {/if}
  </label>
</div>
