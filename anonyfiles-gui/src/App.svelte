<script>
  import DropZone from './lib/DropZone.svelte';
  import TextAnonymizer from './lib/TextAnonymizer.svelte';

  let droppedText = '';

  function handleDrop(event) {
    // Si fichier texte, lecture du contenu...
    if (event.detail && event.detail.files) {
      const file = event.detail.files[0];
      if (file && file.type.startsWith('text/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
          droppedText = e.target.result;
        };
        reader.readAsText(file);
      }
    }
  }
</script>

<!-- Police moderne (exemple: Inter) -->
<svelte:head>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@700;400&display=swap" rel="stylesheet" />
</svelte:head>

<div class="min-h-screen flex flex-col items-center justify-center bg-zinc-900 font-sans">
  <div class="bg-zinc-900 rounded-2xl shadow-2xl border border-zinc-800 max-w-md w-full mx-4 mt-10 mb-10 p-8 flex flex-col gap-6">
    <!-- HEADER / LOGO -->
    <div>
      <h1 class="text-3xl font-extrabold select-none" style="font-family: Inter, sans-serif;">
        <span class="text-blue-400">anonyfiles</span><span class="text-zinc-200">GUI</span>
      </h1>
      <a href="https://github.com/simongrossi" target="_blank"
         class="text-xs text-blue-300 hover:underline ml-1">@simongrossi</a>
    </div>

    <!-- DROPZONE -->
    <DropZone class="mb-2" on:drop={handleDrop}>
      <span class="text-zinc-200">Déposez vos fichiers ici ou cliquez pour sélectionner.</span>
    </DropZone>

    <!-- ANONYMIZER -->
    <TextAnonymizer fileContent={droppedText} />
  </div>
</div>
