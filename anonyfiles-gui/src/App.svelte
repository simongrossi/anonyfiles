<script>
  import DropZone from './lib/DropZone.svelte';
  import TextAnonymizer from './lib/TextAnonymizer.svelte';
  let droppedContent = '';

  function handleFileContent(event) {
    droppedContent = event.detail.content;
  }
</script>

<div class="main-wrapper">
  <div class="card">
    <h1>Anonyfiles GUI</h1>
    <p class="subtitle">Glissez-déposez un fichier texte ici, ou cliquez pour sélectionner</p>

    <DropZone on:fileContent={handleFileContent} />
    <TextAnonymizer bind:fileContent={droppedContent} />

    <h3>Contenu drag & drop :</h3>
    <textarea bind:value={droppedContent} rows="10" placeholder="Aperçu du contenu..." />
  </div>
</div>

<style>
  @import './styles.css';
</style>
