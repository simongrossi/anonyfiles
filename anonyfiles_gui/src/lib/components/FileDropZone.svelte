<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let fileName: string = '';
  export let id: string = 'file-upload-' + Math.random().toString(36).substring(2, 9);
  export let accept: string = ".txt,.csv,.xlsx,.docx,.pdf,.json";
  export let dropZoneId: string;

  const dispatch = createEventDispatcher();
  let internalDragActive = false;

  function handleDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    internalDragActive = false;
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      dispatch('file', { file: files[0], zoneId: dropZoneId });
    }
  }

  function handleChange(event: Event) {
    const target = event.target as HTMLInputElement;
    const files = target?.files;
    if (files && files.length > 0) {
      dispatch('file', { file: files[0], zoneId: dropZoneId });
    }
    if (target) {
      target.value = '';
    }
  }

  function handleDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    internalDragActive = true;
  }

  function handleDragLeave(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    const relatedTarget = event.relatedTarget as Node;
    if (!event.currentTarget || !(event.currentTarget as Node).contains(relatedTarget)) {
      internalDragActive = false;
    }
  }
</script>

<div
  role="group"
  class="dropzone border-2 border-dashed rounded-xl py-0.5 px-3 text-center mb-4 min-h-[60px] transition-colors duration-200 ease-in-out {internalDragActive ? 'border-blue-600 bg-blue-50 dark:border-blue-500 dark:bg-zinc-700' : 'bg-white dark:bg-zinc-800 border-gray-300 dark:border-gray-600 hover:border-blue-500 dark:hover:border-blue-400'}"
  on:drop={handleDrop}
  on:dragover={handleDragOver}
  on:dragleave={handleDragLeave}
>
  <label for={id} class="cursor-pointer w-full h-full flex flex-col justify-center items-center p-1">
    <div class="text-zinc-500 dark:text-zinc-400 mb-1 text-sm">
      <svg class="mx-auto h-5 w-5 text-gray-400 dark:text-gray-500" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
        <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
      Déposez un fichier ou <span class="font-semibold text-blue-600 dark:text-blue-400">cliquez pour parcourir</span>
      {#if accept && accept !== "*/*"}
        <span class="text-xs mt-1 block">Formats : {accept.split(',').map(ext => ext.trim()).join(', ')}</span>
      {:else}
        <span class="text-xs mt-1 block">Tous types de fichiers</span>
      {/if}
    </div>
    <input
      {id}
      type="file"
      {accept}
      class="sr-only"
      on:change={handleChange}
    />
    {#if fileName}
      <span class="mt-2 text-sm font-semibold text-blue-700 dark:text-blue-300 break-all" title={fileName}>
        {fileName.length > 30 ? fileName.substring(0,27) + '...' : fileName }
      </span>
    {/if}
  </label>
</div>

<style>
  /* Les styles pour .dropzone--active ont été déplacés dans l'attribut class du div ci-dessus. */
  /* min-height: 40px; était redondant. */

  .sr-only { 
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border-width: 0;
  }
</style>