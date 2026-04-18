<script lang="ts">
  import { open, save } from '@tauri-apps/plugin-dialog';
  import { readTextFile, writeTextFile } from '@tauri-apps/plugin-fs';
  import { invoke } from '@tauri-apps/api/core';
  import { parse, stringify } from 'yaml';
  import { debugError } from '$lib/utils/api';
  import { isTauri } from '$lib/utils/runtime';

  let status: string | null = null;

  async function exportConfig() {
    if (!isTauri()) return;
    try {
      const config = await invoke('load_config_command');
      const yaml = stringify(config);
      const filePath = await save({ filters: [{ name: 'YAML', extensions: ['yaml', 'yml'] }] });
      if (filePath) {
        await writeTextFile(filePath as string, yaml);
        status = '✅ Configuration exportée';
      }
    } catch (e) {
      debugError(e);
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
      debugError(e);
      status = 'Erreur lors de l\'import';
    }
  }
</script>

<div class="flex flex-wrap items-center gap-2" class:hidden={!isTauri()}>
  <button type="button" class="ui-btn-secondary" on:click={exportConfig}>
    Exporter la configuration
  </button>
  <button type="button" class="ui-btn-secondary" on:click={importConfig}>
    Importer une configuration
  </button>
  {#if status}
    <span class="text-xs text-zinc-500 dark:text-zinc-400">{status}</span>
  {/if}
</div>
