<script>
  import { invoke } from '@tauri-apps/api/tauri';

  export let fileContent = '';
  let inputText = '';
  let outputText = '';
  let isLoading = false;

  async function anonymize() {
    if (!inputText.trim()) return;
    isLoading = true;
    try {
      // Appel vers Rust -> Python via la commande enregistrée dans main.rs
      const result = await invoke('anonymize_text', { input: inputText });
      outputText = result;
    } catch (error) {
      outputText = 'Erreur lors de l’anonymisation : ' + error;
    } finally {
      isLoading = false;
    }
  }

  // Synchronise le champ si un fichier est glissé/déposé
  $: if (fileContent) {
    inputText = fileContent;
    outputText = '';
  }
</script>

<div class="anonymizer">
  <textarea
    bind:value={inputText}
    placeholder="Texte à anonymiser"
    rows="6"
  ></textarea>

  <button on:click={anonymize} disabled={isLoading}>
    {isLoading ? 'Traitement en cours…' : 'Anonymiser'}
  </button>

  <textarea
    bind:value={outputText}
    placeholder="Texte anonymisé"
    rows="6"
    readonly
  ></textarea>
</div>

<style>
  .anonymizer {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  textarea {
    width: 100%;
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid #444;
    font-size: 1rem;
    background-color: #fff;
    color: #000;
    resize: vertical;
    box-sizing: border-box;
  }

  textarea[readonly] {
    background-color: #f8f8f8;
  }

  button {
    padding: 0.75rem;
    font-size: 1rem;
    border-radius: 8px;
    background-color: #646cff;
    color: white;
    border: none;
    cursor: pointer;
    transition: background-color 0.3s ease;
  }

  button:disabled {
    background-color: #999;
    cursor: wait;
  }

  button:hover:enabled {
    background-color: #535bf2;
  }
</style>
