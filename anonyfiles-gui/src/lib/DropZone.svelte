<script>
  import { createEventDispatcher } from 'svelte';
  import { readTextFile } from "@tauri-apps/api/fs";

  const dispatch = createEventDispatcher();
  let dragging = false;

  function onDrop(event) {
    event.preventDefault();
    dragging = false;
    const files = event.dataTransfer.files;
    if (files.length) {
      handleFile(files[0]);
    }
  }

  function onDragOver(event) {
    event.preventDefault();
    dragging = true;
  }

  function onDragLeave() {
    dragging = false;
  }

  async function handleFile(file) {
    if (file.path) {
      const content = await readTextFile(file.path);
      dispatch('fileContent', { content });
    } else {
      const content = await file.text();
      dispatch('fileContent', { content });
    }
  }
</script>

<div
  class="drop-zone"
  on:drop={onDrop}
  on:dragover={onDragOver}
  on:dragleave={onDragLeave}
  class:dragging={dragging}
  tabindex="0"
  role="button"
  on:click={() => document.getElementById('fileInput').click()}
  on:keydown={(e) => { if(e.key === 'Enter' || e.key === ' ') document.getElementById('fileInput').click(); }}
>
  <p>Glissez-déposez un fichier texte ici, ou cliquez pour sélectionner</p>
  <input
    type="file"
    accept=".txt"
    on:change={(e) => handleFile(e.target.files[0])}
    style="display: none;"
    id="fileInput"
  />
</div>
