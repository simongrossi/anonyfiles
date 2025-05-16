<script>
  import { invoke } from "@tauri-apps/api/tauri";
  import { readTextFile, writeTextFile } from "@tauri-apps/api/fs";
  import { open, save } from "@tauri-apps/api/dialog";
  export let fileContent = '';
  let anonymizedContent = '';

  const handleFile = async (event) => {
    const file = event.target.files[0];
    if (file) {
      fileContent = await file.text();
    }
  };

  const anonymizeText = async () => {
    anonymizedContent = await invoke('anonymize_text', { text: fileContent });
  };

  const saveAnonymized = async () => {
    const path = await save({ filters: [{ name: 'Text', extensions: ['txt'] }] });
    if (path) {
      await writeTextFile(path, anonymizedContent);
    }
  };

  const openFile = async () => {
    const selected = await open({ filters: [{ name: 'Text', extensions: ['txt'] }] });
    if (selected) {
      fileContent = await readTextFile(selected);
    }
  };
</script>

<div>
  <h2>Anonymiseur de texte</h2>
  <input type="file" accept=".txt" on:change={handleFile} />
  <button on:click={openFile} tabindex="0">Ouvrir un fichier</button>
  <button on:click={anonymizeText} tabindex="0">Anonymiser</button>
  <button on:click={saveAnonymized} tabindex="0">Enregistrer</button>

  <h3>Texte original :</h3>
  <textarea bind:value={fileContent} rows="10" cols="80"></textarea>

  <h3>Texte anonymisé :</h3>
  <textarea bind:value={anonymizedContent} rows="10" cols="80"></textarea>
</div>
