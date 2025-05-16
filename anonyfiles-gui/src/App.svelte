<script>
  import DropZone from './lib/DropZone.svelte';
  import TextAnonymizer from './lib/TextAnonymizer.svelte';
  let droppedContent = '';

  function handleFileContent(event) {
    droppedContent = event.detail.content;
  }
</script>

<main>
  <h1>Anonyfiles GUI</h1>

  <DropZone on:fileContent={handleFileContent} />
  <TextAnonymizer bind:fileContent={droppedContent} />

  <h3>Contenu drag & drop :</h3>
  <textarea bind:value={droppedContent} rows="10" cols="80"></textarea>
</main>
