<script lang="ts">
  import { onMount } from 'svelte';
  import { open, save } from '@tauri-apps/api/dialog';
  import { readTextFile, writeFile } from '@tauri-apps/api/fs';
  import { invoke } from '@tauri-apps/api/tauri';
  import { parse, stringify } from 'yaml';

  let status: string | null = null;

  function isTauri(): boolean {
    return typeof window !== 'undefined' && typeof (window as any).__TAURI_IPC__ === 'function';
  }

  async function exportConfig() {
    if (!isTauri()) return;
    try {
      const config = await invoke('load_config_command');
      const yaml = stringify(config);
      const filePath = await save({ filters: [{ name: 'YAML', extensions: ['yaml', 'yml'] }] });
      if (filePath) {
        await writeFile({ path: filePath as string, contents: yaml });
        status = '✅ Configuration exportée';
      }
    } catch (e) {
      console.error(e);
      status = 'Erreur lors de l\'export';
    }
  }

  async function importConfig() {
    if (!isTauri()) return;
    try {
      const selected = await open({ filters: [{ name: 'YAML', extensions: ['yaml', 'yml'] }] });
      if (typeof selected === 'string') {
        const content = await readTextFile(selected);
        const json = parse(content);
        await invoke('save_config_command', json);
        status = '✅ Configuration importée';
      }
    } catch (e) {
      console.error(e);
      status = 'Erreur lors de l\'import';
    }
  }
</script>

<div class="space-x-4 my-4" class:hidden={!isTauri()}>
  <button class="btn" on:click={exportConfig}>Exporter la configuration</button>
  <button class="btn" on:click={importConfig}>Importer une configuration</button>
  {#if status}
    <span class="text-sm ml-2">{status}</span>
  {/if}
</div>
