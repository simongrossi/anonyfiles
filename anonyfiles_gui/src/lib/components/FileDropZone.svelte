<!-- #anonyfiles\anonyfiles_gui\src\lib\components\FileDropZone.svelte -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let fileName: string = '';
  export let dragActive: boolean = false;

  const dispatch = createEventDispatcher();

  function onDrop(event: DragEvent) {
    event.preventDefault();
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      dispatch('file', { file: files[0] });
    }
  }

  function onChange(event: Event) {
    const files = (event.target as HTMLInputElement)?.files;
    if (files && files.length > 0) {
      dispatch('file', { file: files[0] });
    }
  }

  function onDragOver(event: DragEvent) {
    event.preventDefault();
    dispatch('dragover');
  }

  function onDragLeave(event: DragEvent) {
    event.preventDefault();
    dispatch('dragleave');
  }
</script>

<div
  role="region"
  aria-label="Zone de dépôt de fichiers"
  class="dropzone border-2 border-dashed rounded-xl p-4 text-center mb-4 transition bg-white dark:bg-zinc-900"
  class:dropzone--active={dragActive}
  on:drop={onDrop}
  on:dragover={onDragOver}
  on:dragleave={onDragLeave}
>
  <label for="file-upload" class="cursor-pointer block">
    <div class="text-zinc-400 mb-2">
      Déposez un fichier ou cliquez pour parcourir<br/>
      <span class="text-xs">Formats supportés : .txt, .csv, .xlsx, .docx, .pdf, .json</span>
    </div>
    <input
      id="file-upload"
      type="file"
      accept=".txt,.csv,.xlsx,.docx,.pdf,.json"
      class="hidden"
      on:change={onChange}
    />
    {#if fileName}
      <span class="font-semibold text-blue-600">{fileName}</span>
    {/if}
  </label>
</div>


<style>
  .dropzone {
    min-height: 80px;
    border-color: #d1d5db;
    transition: border-color 0.2s, background 0.2s;
  }
  .dropzone--active {
    border-color: #2563eb;
    background: #e0e7ff;
  }
</style>
