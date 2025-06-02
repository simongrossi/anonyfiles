<!-- #anonyfiles/anonyfiles_gui/src/lib/components/ReleasesView.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';

  interface ReleaseEntry {
    version: string;
    date: string;
    entries: string[];
  }

  let changelog: ReleaseEntry[] = [];

  onMount(async () => {
    const res = await fetch('/data/changelog.json');
    changelog = await res.json();
  });
</script>

<div class="space-y-6">
  <h2 class="text-3xl font-bold text-gray-800 dark:text-white">Nouveautés & Mises à jour</h2>

  <div class="p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
    <h3 class="text-xl font-semibold text-gray-700 dark:text-gray-200">
      Synthèse des fonctionnalités clés
    </h3>
    <ul class="list-disc list-inside mt-2 text-gray-600 dark:text-gray-400 space-y-1">
      <li>Anonymisation multi-format : <code>.txt</code>, <code>.csv</code>, <code>.docx</code>, <code>.xlsx</code>, <code>.pdf</code>, <code>.json</code></li>
      <li>Remplacement positionnel précis (via offsets spaCy) pour tous les formats</li>
      <li>Règles personnalisées (simples ou regex) avec priorité sur spaCy</li>
      <li>Configuration par fichier YAML (entités, remplacements, exclusions…)</li>
      <li>Journalisation complète (audit + mapping) pour traçabilité et désanonymisation</li>
      <li>Création automatique de sous-dossiers par exécution avec timestamp</li>
      <li>Désanonymisation possible via mapping CSV</li>
      <li>Interface graphique complète : drag & drop, preview, split view avant/après, responsive</li>
      <li>Audit log interactif : règles appliquées, type, nombre de remplacements</li>
      <li>API FastAPI sécurisée et asynchrone avec logs unifiés</li>
    </ul>
  </div>

  {#each changelog as release (release.version)}
    <div class="p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
      <h3 class="text-xl font-semibold text-gray-700 dark:text-gray-200">
        Version {release.version} ({release.date})
      </h3>
      <ul class="list-disc list-inside mt-2 text-gray-600 dark:text-gray-400 space-y-1">
        {#each release.entries as entry}
          <li>{@html entry}</li>
        {/each}
      </ul>
    </div>
  {/each}

  <div class="text-center mt-8">
    <p class="text-sm text-gray-500 dark:text-gray-400">
      Consultez le changelog complet sur
      <a
        href="https://github.com/simongrossi/anonyfiles/commits/main"
        target="_blank"
        rel="noopener noreferrer"
        class="text-blue-500 hover:underline"
      >
        GitHub
      </a>
      .
    </p>
  </div>
</div>
