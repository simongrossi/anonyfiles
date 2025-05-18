<script>
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  function handleDrop(event) {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      dispatch('fileContent', { content: reader.result });
    };
    reader.readAsText(file);
  }

  function handleDragOver(event) {
    event.preventDefault();
  }

  function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      dispatch('fileContent', { content: reader.result });
    };
    reader.readAsText(file);
  }
</script>

<div class="drop-zone"
     on:drop={handleDrop}
     on:dragover={handleDragOver}
     tabindex="0">
  <p>📄 Glissez-déposez un fichier texte ici,<br>ou cliquez pour sélectionner</p>
  <input type="file" accept=".txt" on:change={handleFileSelect} />
</div>

<style>
  .drop-zone {
    border: 2px dashed #888;
    padding: 2rem;
    text-align: center;
    border-radius: 12px;
    background-color: #1a1a1a;
    transition: border-color 0.2s ease, background-color 0.2s ease;
    cursor: pointer;
  }

  .drop-zone:hover {
    border-color: #646cff;
    background-color: #2a2a2a;
  }

  .drop-zone input[type="file"] {
    display: none;
  }

  .drop-zone:focus {
    outline: none;
    border-color: #535bf2;
  }
</style>
