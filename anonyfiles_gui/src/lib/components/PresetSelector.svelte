<!-- #anonyfiles/anonyfiles_gui/src/lib/components/PresetSelector.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { customReplacementRules } from '$lib/stores/customRulesStore';

  let presets: string[] = [];
  let selectedPreset: string | null = null;
  let presetContent: string | null = null;
  let loading = false;
  let error: string | null = null;
  let successMessage: string | null = null;

  function isTauriEnvironment(): boolean {
    return typeof window !== 'undefined' && typeof (window as any).__TAURI_IPC__ === 'function';
  }

  onMount(async () => {
    if (!isTauriEnvironment()) {
      error = "Fonctionnalité disponible uniquement en version bureau (Tauri)";
      return;
    }

    loading = true;
    try {
      const { invoke } = await import('@tauri-apps/api/tauri');
      presets = await invoke<string[]>('list_presets');
    } catch (err) {
      error = 'Erreur lors du chargement des presets';
      console.error(err);
    } finally {
      loading = false;
    }
  });

  async function applyPreset(preset: string | null) {
    if (!preset || !isTauriEnvironment()) return;

    selectedPreset = preset;
    successMessage = null;
    try {
      const { readTextFile } = await import('@tauri-apps/api/fs');
      const { join } = await import('@tauri-apps/api/path');
      const presetPath = await join('public', 'wordlist_presets', preset);
      presetContent = await readTextFile(presetPath);
    } catch (err) {
      console.error('Erreur lors du chargement du preset :', err);
      presetContent = null;
    }
  }

  function injectPreset() {
    if (!presetContent) return;
    try {
      const parsed = JSON.parse(presetContent);
      if (Array.isArray(parsed)) {
        customReplacementRules.update(current => [...current, ...parsed]);
        successMessage = `✅ ${parsed.length} règle(s) ajoutée(s) depuis le preset.`;
      }
    } catch (err) {
      console.error('Erreur lors de l’injection du preset :', err);
    }
  }

  function clearRules() {
    customReplacementRules.set([]);
    successMessage = '🧹 Toutes les règles ont été supprimées.';
  }
</script>

<div class="p-4 space-y-4">
  <h2 class="text-xl font-semibold text-gray-800 dark:text-gray-100">📚 Bibliothèque de règles prédéfinies</h2>

  {#if loading}
    <p class="text-gray-500 italic">Chargement des presets...</p>
  {:else if error}
    <p class="text-red-500">{error}</p>
  {:else if presets.length === 0}
    <p class="text-gray-500 italic">Aucun preset disponible.</p>
  {:else}
    <div class="space-y-2">
      <label for="presetSelect" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Choisir un preset :</label>
      <select
        id="presetSelect"
        bind:value={selectedPreset}
        on:change={() => applyPreset(selectedPreset)}
        class="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-zinc-800 text-gray-800 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
      >
        <option disabled selected value="">-- Sélectionner un preset --</option>
        {#each presets as preset}
          <option value={preset}>{preset}</option>
        {/each}
      </select>

      {#if selectedPreset}
        <div class="mt-2 text-sm text-green-700 dark:text-green-400">
          ✅ Preset <strong>{selectedPreset}</strong> sélectionné.
        </div>
      {/if}

      {#if presetContent}
        <div class="mt-4 text-sm whitespace-pre-wrap bg-zinc-100 dark:bg-zinc-700 p-3 rounded-md border border-gray-300 dark:border-gray-600 max-h-60 overflow-auto">
          <code>{presetContent}</code>
        </div>

        <div class="flex flex-col sm:flex-row gap-4 mt-4">
          <button class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded" on:click={injectPreset}>
            ➕ Appliquer ce preset
          </button>
          <button class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded" on:click={clearRules}>
            🧹 Vider toutes les règles
          </button>
        </div>
      {/if}

      {#if successMessage}
        <div class="mt-4 text-sm text-green-600 dark:text-green-300">{successMessage}</div>
      {/if}
    </div>
  {/if}
</div>
