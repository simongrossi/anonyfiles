<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  export let fileName: string = "";
  export let dragActive: boolean = false;

  const dispatch = createEventDispatcher();

  function onDragOver(event: DragEvent) {
    event.preventDefault();
    dispatch('dragover', event);
  }
  function onDragLeave(event: DragEvent) {
    event.preventDefault();
    dispatch('dragleave', event);
  }
  function onDrop(event: DragEvent) {
    event.preventDefault();
    dispatch('dragleave', event);
    const file = event.dataTransfer?.files?.[0];
    if (file) {
      dispatch('file', { file });
    }
  }
  function onFileInput(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) {
      dispatch('file', { file });
    }
  }
</script>

<div
    class="dropzone {dragActive ? 'bg-blue-50 border-blue-500' : ''}"
    on:dragover={onDragOver}
    on:dragleave={onDragLeave}
    on:drop={onDrop}
    tabindex="0"
>
    <input
        type="file"
        id="fileInput"
        accept=".txt,.csv,.xlsx,.docx,.pdf,.json"
        class="hidden"
        on:change={onFileInput}
    />
    <label for="fileInput" class="cursor-pointer flex flex-col items-center gap-2">
        <span class="text-base font-medium text-zinc-700 dark:text-zinc-200">
            Déposez un fichier ou cliquez pour parcourir
        </span>
        <span class="text-sm text-zinc-500 dark:text-zinc-400">
            Formats supportés : .txt, .csv, .xlsx, .docx, .pdf, .json
        </span>
        {#if fileName}
            <span class="text-blue-800 font-semibold mt-2 dark:text-blue-400">{fileName}</span>
        {/if}
    </label>
</div>
