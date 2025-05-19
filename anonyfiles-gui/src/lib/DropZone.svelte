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

<style>
  .drop-zone {
    border: 2px dashed #ddd;
    padding: 2rem;
    border-radius: 1rem;
    text-align: center;
    transition: background 0.2s, color 0.2s;
    cursor: pointer;
    background: #f1f5f9;    /* Gris clair avec contraste */
    color: #22223b;         /* Texte foncé et lisible */
  }
  .drop-zone.dragging {
    background: #e0e7ef;
    border-color: #3b82f6;
    color: #1e293b;         /* Texte un peu plus foncé */
  }
  input[type="file"] {
    display: none;
  }
</style>

<div
  class="drop-zone {isDragging ? 'dragging' : ''}"
  role="region"
  aria-label="Zone de dépôt de fichiers"
  tabindex="0"
  on:dragover={handleDragOver}
  on:dragleave={handleDragLeave}
  on:drop={handleDrop}
  on:click={handleClick}
  on:keydown={(e) => {
    // accessibilité clavier : touche Espace ou Entrée
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  }}
>
  <slot>
    <p style="margin:0;">Déposez vos fichiers ici ou cliquez pour sélectionner.</p>
  </slot>
  <input
    type="file"
    bind:this={fileInput}
    {accept}
    {multiple}
    on:change={handleFileChange}
  />
</div>
