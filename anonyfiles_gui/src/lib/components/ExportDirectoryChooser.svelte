<script lang="ts">
  import { open } from '@tauri-apps/plugin-dialog';
  let {
    exportDir,
    onDirChange,
  }: { exportDir: string; onDirChange: (dir: string) => void } = $props();

  async function chooseExportDir() {
    const selected = await open({
      directory: true,
      multiple: false
    });
    if (typeof selected === "string") {
      onDirChange(selected);
    }
  }
</script>

<div class="mb-4">
  <button class="btn" on:click={chooseExportDir}>
    Choisir le dossier d’export
  </button>
  {#if exportDir}
    <div class="text-xs mt-1 text-gray-500 truncate">Dossier sélectionné : {exportDir}</div>
  {/if}
</div>
