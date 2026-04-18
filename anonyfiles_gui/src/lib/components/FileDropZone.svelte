<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { FileUp, FileText, X } from 'lucide-svelte';

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

  function handleClear(event: Event) {
    event.preventDefault();
    event.stopPropagation();
    dispatch('clear', { zoneId: dropZoneId });
  }

  $: formats = accept && accept !== '*/*'
    ? accept.split(',').map((ext) => ext.trim().replace(/^\./, '').toUpperCase()).join(' · ')
    : 'Tous formats';

  $: shortName = fileName && fileName.length > 44 ? fileName.slice(0, 41) + '…' : fileName;
</script>

<div
  role="group"
  class="ui-dropzone mb-5 {internalDragActive ? 'ui-dropzone-active' : ''}"
  on:drop={handleDrop}
  on:dragover={handleDragOver}
  on:dragleave={handleDragLeave}
>
  <label for={id} class="absolute inset-0 cursor-pointer rounded-2xl"></label>

  {#if fileName}
    <div class="relative z-10 flex items-center gap-3 rounded-xl bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 px-4 py-3 shadow-card max-w-lg w-full">
      <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-50 dark:bg-brand-900/30 text-brand-600 dark:text-brand-100">
        <FileText size={20} />
      </div>
      <div class="min-w-0 flex-1 text-left">
        <p class="text-sm font-medium text-zinc-900 dark:text-zinc-100 truncate" title={fileName}>{shortName}</p>
        <p class="text-xs text-zinc-500 dark:text-zinc-400">Fichier prêt · clique pour changer</p>
      </div>
      <button
        type="button"
        class="ui-icon-btn relative z-20"
        title="Retirer le fichier"
        aria-label="Retirer le fichier"
        on:click={handleClear}
      >
        <X size={16} />
      </button>
    </div>
  {:else}
    <div class="relative z-10 flex flex-col items-center gap-2 pointer-events-none">
      <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-white dark:bg-zinc-900 text-brand-600 dark:text-brand-100 border border-zinc-200 dark:border-zinc-700 shadow-sm">
        <FileUp size={22} strokeWidth={1.75} />
      </div>
      <p class="text-sm text-zinc-700 dark:text-zinc-200">
        Glisse un fichier ici ou
        <span class="font-semibold text-brand-600 dark:text-brand-100">clique pour parcourir</span>
      </p>
      <p class="text-[11px] uppercase tracking-wider text-zinc-400 dark:text-zinc-500">{formats}</p>
    </div>
  {/if}

  <input
    {id}
    type="file"
    {accept}
    class="sr-only"
    on:change={handleChange}
  />
</div>

<style>
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
