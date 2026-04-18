<!-- #anonyfiles/anonyfiles_gui/src/lib/components/WordlistRuleGenerator.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { invoke } from '@tauri-apps/api/core';
  import { customReplacementRules } from '$lib/stores/customRulesStore';
  import { v4 as uuidv4 } from 'uuid';
  import { get } from 'svelte/store';
  import { Brain, Plus, Upload } from 'lucide-svelte';
  import { debugError } from '$lib/utils/api';

  let prefix = 'WORD_';
  let fixedReplacement = '';
  let useSequential = true;

  let fileContent: string[] = [];
  let uploadedFileName = '';
  let selectedPreset = '';
  let availablePresets: string[] = [];

  onMount(async () => {
    try {
      availablePresets = await invoke('list_presets');
    } catch (error) {
      debugError('Erreur lors du chargement des presets:', error);
    }
  });

  function handleFileUpload(event: Event) {
    const target = event.target as HTMLInputElement;
    const file = target?.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        const text = reader.result as string;
        fileContent = text.split('\n').map((line) => line.trim()).filter(Boolean);
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
        debugError(`Erreur chargement du preset ${selectedPreset}:`, error);
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
      isRegex: false,
    }));
    customReplacementRules.set([...existingRules, ...newRules]);
  }
</script>

<div class="space-y-5">
  <div class="flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-200">
    <Brain size={16} class="text-brand-500" />
    <span class="font-medium">Générateur de règles via wordlist</span>
  </div>

  <div>
    <label for="wordlistFile" class="ui-field-label flex items-center gap-1.5">
      <Upload size={12} />
      Importer un fichier texte (.txt)
    </label>
    <input
      id="wordlistFile"
      type="file"
      accept=".txt"
      on:change={handleFileUpload}
      class="block w-full text-sm text-zinc-700 dark:text-zinc-200
             file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0
             file:bg-zinc-100 dark:file:bg-zinc-700 file:text-zinc-700 dark:file:text-zinc-100
             hover:file:bg-zinc-200 dark:hover:file:bg-zinc-600 file:cursor-pointer file:font-medium
             file:text-xs"
    />
  </div>

  <div>
    <label for="presetSelect" class="ui-field-label">Ou choisir un modèle JSON</label>
    <select
      id="presetSelect"
      bind:value={selectedPreset}
      on:change={applyPreset}
      class="ui-input"
    >
      <option value="">— Sélectionner un preset —</option>
      {#each availablePresets as file}
        <option value={file}>{file}</option>
      {/each}
    </select>
  </div>

  <div>
    <span class="ui-field-label">Mode de remplacement</span>
    <div class="flex flex-wrap gap-4">
      <label class="inline-flex items-center gap-2 cursor-pointer text-sm text-zinc-700 dark:text-zinc-200">
        <input
          type="radio"
          name="mode"
          bind:group={useSequential}
          value={true}
          class="h-4 w-4 text-brand-600 border-zinc-300 dark:border-zinc-600 dark:bg-zinc-900 focus:ring-brand-500/40"
        />
        Remplacement séquentiel
      </label>
      <label class="inline-flex items-center gap-2 cursor-pointer text-sm text-zinc-700 dark:text-zinc-200">
        <input
          type="radio"
          name="mode"
          bind:group={useSequential}
          value={false}
          class="h-4 w-4 text-brand-600 border-zinc-300 dark:border-zinc-600 dark:bg-zinc-900 focus:ring-brand-500/40"
        />
        Remplacement fixe
      </label>
    </div>
  </div>

  {#if useSequential}
    <div>
      <label for="prefix" class="ui-field-label">Préfixe de remplacement</label>
      <input id="prefix" type="text" bind:value={prefix} class="ui-input" placeholder="WORD_" />
      <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
        Ex : <code class="font-mono text-zinc-600 dark:text-zinc-300">MOT_</code>
        → <code class="font-mono text-zinc-600 dark:text-zinc-300">MOT_001, MOT_002</code>
      </p>
    </div>
  {:else}
    <div>
      <label for="fixedReplacement" class="ui-field-label">Texte de remplacement fixe</label>
      <input id="fixedReplacement" type="text" bind:value={fixedReplacement} class="ui-input" placeholder="[REDACTED]" />
    </div>
  {/if}

  <div class="flex items-center justify-between flex-wrap gap-3">
    <button
      type="button"
      on:click={generateRules}
      class="ui-btn-primary"
      disabled={fileContent.length === 0}
    >
      <Plus size={16} />
      Générer et ajouter les règles
    </button>
    {#if fileContent.length > 0}
      <p class="text-xs text-zinc-500 dark:text-zinc-400">
        {fileContent.length} mots chargés depuis
        <strong class="text-zinc-700 dark:text-zinc-200">{uploadedFileName}</strong>
      </p>
    {/if}
  </div>
</div>
