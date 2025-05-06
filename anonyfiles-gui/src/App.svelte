<script lang="ts">
  import { invoke } from '@tauri-apps/api/tauri';
  import { open } from '@tauri-apps/api/dialog';

  let droppedFilePath = '';
  let isProcessing = false;
  let success = false;

  async function handleDrop(event: DragEvent) {
    event.preventDefault();
    const files = event.dataTransfer?.files;
    if (!files || files.length === 0) return;
    const filePath = files[0].path;
    await processFile(filePath);
  }

  async function browseFile() {
    const selected = await open({ multiple: false });
    if (typeof selected === 'string') {
      await processFile(selected);
    }
  }

  async function processFile(filePath: string) {
    isProcessing = true;
    droppedFilePath = filePath;
    success = false;
    try {
      await invoke('process_file', { path: filePath });
      success = true;
    } catch (e) {
      console.error(e);
    } finally {
      isProcessing = false;
    }
  }
</script>

<style>
  .dropzone {
    border: 2px dashed #aaa;
    padding: 2rem;
    text-align: center;
    margin: 2rem;
    border-radius: 10px;
    transition: border-color 0.2s;
  }
  .dropzone:hover {
    border-color: #333;
  }
  button {
    margin-top: 1rem;
    padding: 0.5rem 1rem;
    font-size: 1rem;
  }
  .processing {
    color: orange;
    text-align: center;
  }
  .success {
    color: green;
    text-align: center;
  }
</style>

<div class="dropzone" on:drop={handleDrop} on:dragover|preventDefault>
  <p>Glisser-déposer un fichier ici</p>
  <button on:click={browseFile}>Ou parcourir</button>
</div>

{#if isProcessing}
  <p class="processing">Traitement en cours...</p>
{:else if success}
  <p class="success">Traitement réussi !</p>
{:else if droppedFilePath}
  <p style="text-align: center;">Fichier sélectionné : {droppedFilePath}</p>
{/if}
