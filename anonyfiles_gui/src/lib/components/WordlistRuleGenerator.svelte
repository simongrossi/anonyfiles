<!-- #anonyfiles/anonyfiles_gui/src/lib/components/WordlistRuleGenerator.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { invoke } from '@tauri-apps/api/tauri';
  import { customReplacementRules } from '$lib/stores/customRulesStore';
  import { v4 as uuidv4 } from 'uuid';
  import { get } from 'svelte/store';

  let prefix = 'WORD_';
  let fixedReplacement = '';
  let useSequential = true;

  let fileContent: string[] = [];
  let uploadedFileName = '';
  let selectedPreset = '';
  let availablePresets: string[] = [];

  // Charger les presets disponibles dans public/presets/
  onMount(async () => {
    try {
      availablePresets = await invoke('list_presets');
    } catch (error) {
      console.error('Erreur lors du chargement des presets:', error);
    }
  });

  function handleFileUpload(event: Event) {
    const target = event.target as HTMLInputElement;
    const file = target?.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        const text = reader.result as string;
        fileContent = text.split('\n').map(line => line.trim()).filter(Boolean);
        uploadedFileName = file.name;
      };
      reader.readAsText(file);
    }
  }

  async function applyPreset() {
    if (selectedPreset) {
      try {
        const response = await fetch(`/presets/${selectedPreset}`);
        const json: string[] = await response.json();
        fileContent = json.filter(Boolean);
        uploadedFileName = selectedPreset;
      } catch (error) {
        console.error(`Erreur chargement du preset ${selectedPreset}:`, error);
      }
    }
  }

  function generateRules() {
    const existingRules = get(customReplacementRules);
    const newRules = fileContent.map((word, index) => ({
      pattern: word,
      replacement: useSequential
        ? `${prefix}${(index + 1).toString().padStart(3, '0')}`
        : fixedReplacement || uuidv4(),
      isRegex: false
    }));
    customReplacementRules.set([...existingRules, ...newRules]);
  }
</script>

<div class="p-6 space-y-6 bg-white rounded shadow">
  <h2 class="text-xl font-semibold">🧠 Générateur de règles via wordlist</h2>

  <div class="flex flex-col space-y-2">
    <label for="wordlistFile" class="font-medium">Importer un fichier texte (.txt)</label>
    <input id="wordlistFile" type="file" accept=".txt" on:change={handleFileUpload} />
  </div>

  <div class="flex flex-col space-y-2">
    <label for="presetSelect" class="font-medium">Ou choisir un modèle JSON :</label>
    <select id="presetSelect" bind:value={selectedPreset} on:change={applyPreset} class="p-2 border rounded">
      <option value="">-- Sélectionner un preset --</option>
      {#each availablePresets as file}
        <option value={file}>{file}</option>
      {/each}
    </select>
  </div>

  <div class="flex items-center gap-4">
    <label class="flex items-center gap-2">
      <input type="radio" name="mode" bind:group={useSequential} value={true} />
      Remplacement séquentiel
    </label>
    <label class="flex items-center gap-2">
      <input type="radio" name="mode" bind:group={useSequential} value={false} />
      Remplacement fixe
    </label>
  </div>

  {#if useSequential}
    <div class="flex flex-col space-y-2">
      <label for="prefix" class="font-medium">Préfixe de remplacement</label>
      <input id="prefix" type="text" bind:value={prefix} class="p-2 border rounded" />
      <span class="text-sm text-gray-500">Ex : MOT_ → MOT_001, MOT_002</span>
    </div>
  {:else}
    <div class="flex flex-col space-y-2">
      <label for="fixedReplacement" class="font-medium">Texte de remplacement fixe</label>
      <input id="fixedReplacement" type="text" bind:value={fixedReplacement} class="p-2 border rounded" />
    </div>
  {/if}

  <button
    on:click={generateRules}
    class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded"
    disabled={fileContent.length === 0}
  >
    ➕ Générer et ajouter les règles
  </button>

  {#if fileContent.length > 0}
    <p class="text-sm text-gray-600">{fileContent.length} mots chargés depuis <strong>{uploadedFileName}</strong>.</p>
  {/if}
</div>
