<script>
  export let fileContent = '';
  let inputText = '';
  let outputText = '';

  function anonymize() {
    // Remplacement de mots fictif pour exemple
    outputText = inputText.replace(/\b(Nom|Prénom|Adresse)\b/gi, '[ANONYME]');
  }

  // Synchroniser si un fichier est déposé
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

  <button on:click={anonymize}>Anonymiser</button>

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

  button:hover {
    background-color: #535bf2;
  }
</style>
