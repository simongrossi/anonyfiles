<script>
  import DropZone from './lib/DropZone.svelte';
  import TextAnonymizer from './lib/TextAnonymizer.svelte';

  let droppedContent = '';

  function handleDrop(event) {
    // Récupère le contenu du premier fichier texte drag & drop
    const files = event.detail.files;
    if (files && files.length > 0) {
      const file = files[0];
      const reader = new FileReader();
      reader.onload = (e) => {
        droppedContent = e.target.result;
      };
      reader.readAsText(file);
    }
  }
</script>

<div class="min-h-screen bg-zinc-900 py-8 px-4">
  <div class="max-w-3xl mx-auto bg-zinc-800 rounded-2xl p-8 shadow-xl flex flex-col gap-8">
    <h1 class="text-3xl font-semibold text-white mb-2">Anonyfiles GUI</h1>
    <p class="text-zinc-200 mb-2">
      Glissez-déposez un fichier texte ici, ou cliquez pour sélectionner
    </p>
    <!-- DropZone avec gestion d'événement -->
    <DropZone accept=".txt" on:drop={handleDrop} />
    <!-- Composant d'anonymisation (transmet le contenu drag&drop) -->
    <TextAnonymizer fileContent={droppedContent} />
    <!-- Zone de preview drag & drop -->
    <div>
      <h2 class="text-lg font-bold text-white mt-8 mb-2">Contenu drag & drop :</h2>
      <textarea
        class="w-full rounded-xl border border-zinc-400 p-3 min-h-[120px] bg-zinc-900 text-white"
        placeholder="Aperçu du contenu..." readonly
        bind:value={droppedContent}
      />
    </div>
  </div>
</div>
