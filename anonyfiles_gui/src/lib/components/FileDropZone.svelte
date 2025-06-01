<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let fileName: string = ''; // Pour afficher le nom du fichier sélectionné
  // ID unique pour l'élément input HTML interne, généré aléatoirement par défaut si non fourni
  export let id: string = 'file-upload-' + Math.random().toString(36).substring(2, 9); 
  export let accept: string = ".txt,.csv,.xlsx,.docx,.pdf,.json"; // Types de fichiers acceptés par défaut
  export let dropZoneId: string; // Identifiant unique pour CETTE instance de dropzone (DOIT être passé par le parent)

  const dispatch = createEventDispatcher();
  let internalDragActive = false; // Gérer l'état visuel du drag localement

  function handleDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation(); // Empêcher la propagation aux éléments parents
    internalDragActive = false;
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      // Dispatch l'événement 'file' avec l'objet File ET l'identifiant de la zone
      dispatch('file', { file: files[0], zoneId: dropZoneId });
    }
  }

  function handleChange(event: Event) {
    const target = event.target as HTMLInputElement;
    const files = target?.files;
    if (files && files.length > 0) {
      // Dispatch l'événement 'file' avec l'objet File ET l'identifiant de la zone
      dispatch('file', { file: files[0], zoneId: dropZoneId });
    }
    // Important : Réinitialiser la valeur de l'input pour permettre de re-sélectionner le même fichier
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
    // S'assurer qu'on quitte vraiment la zone pour éviter le clignotement sur les éléments enfants
    const relatedTarget = event.relatedTarget as Node;
    if (!event.currentTarget || !(event.currentTarget as Node).contains(relatedTarget)) {
        internalDragActive = false;
    }
  }
</script>

<div
  role="group" 
  class="dropzone border-2 border-dashed rounded-xl p-4 text-center mb-4 transition-colors duration-200 ease-in-out
         bg-white dark:bg-zinc-800 
         border-gray-300 dark:border-gray-600
         hover:border-blue-500 dark:hover:border-blue-400"
  class:dropzone--active={internalDragActive}
  on:drop={handleDrop} on:dragover={handleDragOver}
  on:dragleave={handleDragLeave}
>
  <label for={id} class="cursor-pointer block w-full h-full flex flex-col justify-center items-center p-2">
    <div class="text-zinc-500 dark:text-zinc-400 mb-2">
      <svg class="mx-auto h-10 w-10 text-gray-400 dark:text-gray-500" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
        <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
      Déposez un fichier ou <span class="font-semibold text-blue-600 dark:text-blue-400">cliquez pour parcourir</span><br/>
      {#if accept && accept !== "*/*"} <span class="text-xs mt-1">Formats : {accept.split(',').map(ext => ext.trim()).join(', ')}</span>
      {:else}
        <span class="text-xs mt-1">Tous types de fichiers</span>
      {/if}
    </div>
    <input
      {id} type="file"
      {accept} class="sr-only" on:change={handleChange}
    />
    {#if fileName} <span class="mt-2 text-sm font-semibold text-blue-700 dark:text-blue-300 break-all" title={fileName}>
        {fileName.length > 30 ? fileName.substring(0,27) + '...' : fileName }
      </span>
    {/if}
  </label>
</div>

<style>
  .dropzone {
    min-height: 120px; 
  }
  .dropzone--active {
    border-color: #2563eb !important; /* Important pour s'assurer que ça override le style de base */
    background-color: #eff6ff !important;
  }
  .dark .dropzone--active {
    border-color: #3b82f6 !important;
    background-color: #1f2937 !important; /* Un fond un peu plus sombre pour le dark mode actif */
  }
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