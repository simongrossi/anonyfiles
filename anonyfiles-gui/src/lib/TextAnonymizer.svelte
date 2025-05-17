<script>
  import { invoke } from "@tauri-apps/api/tauri";
  let inputText = "";
  let outputText = "";

  async function anonymize() {
    try {
      outputText = await invoke("anonymize_text", { input: inputText });
    } catch (e) {
      outputText = "Erreur: " + e;
    }
  }
</script>

<textarea bind:value={inputText} placeholder="Texte à anonymiser"></textarea>
<button on:click={anonymize}>Anonymiser</button>
<textarea readonly bind:value={outputText} placeholder="Texte anonymisé"></textarea>
