<!-- #anonyfiles/anonyfiles_gui/src/lib/components/ReleasesView.svelte -->
<script lang="ts">
  import { Sparkles, Github } from 'lucide-svelte';

  const highlights = [
    'Démarrage du projet avec anonymisation texte simple (.txt), configuration YAML, moteur spaCy et remplacement basique.',
    'Support multi-format progressif : .csv avec en-têtes, .docx, .xlsx, puis .pdf et .json, avec prévisualisation intégrée.',
    'Règles personnalisées (texte ou regex), priorisées sur les entités spaCy.',
    "Système d'audit complet : mapping CSV, journal de traitement, fichier log horodaté.",
    'Désanonymisation basée sur le fichier de mapping CSV exportable.',
    'Refactor du moteur : traitements centralisés, séparation logique / analyse / remplacement.',
    'Interface graphique Tauri + Svelte : drag & drop, preview dynamique, comparaison avant/après, responsive.',
    'API FastAPI : endpoints d\'anonymisation, suivi de statut, téléchargement, logs intégrés.',
    'Route DELETE /api/jobs/<id> pour supprimer les jobs obsolètes, intégrée dans la GUI.',
    'Ergonomie desktop : layout revu, header fixe, sidebar compacte en mobile.',
    'Gestion dynamique des règles personnalisées : export/import JSON, détection de doublons.',
    'Modernisation continue du design : composants épurés, dark mode, refonte de la drop-zone.',
  ];
</script>

<div class="w-full max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 pb-10">
  <div class="mb-5 flex items-center gap-3">
    <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 dark:bg-brand-900/30 text-brand-600 dark:text-brand-100">
      <Sparkles size={20} />
    </div>
    <div>
      <h1 class="text-lg font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
        Nouveautés & mises à jour
      </h1>
      <p class="text-xs text-zinc-500 dark:text-zinc-400">
        Condensé chronologique des principales évolutions.
      </p>
    </div>
  </div>

  <section class="ui-section">
    <header class="ui-section-header">
      <span class="ui-section-title">Résumé des évolutions</span>
    </header>
    <div class="ui-section-body">
      <ul class="space-y-3 text-sm text-zinc-700 dark:text-zinc-200">
        {#each highlights as entry}
          <li class="flex items-start gap-3">
            <span
              class="mt-1.5 h-1.5 w-1.5 rounded-full bg-brand-500 shrink-0"
              aria-hidden="true"
            ></span>
            <span>{entry}</span>
          </li>
        {/each}
      </ul>
    </div>
  </section>

  <p class="mt-6 text-center text-xs text-zinc-500 dark:text-zinc-400">
    Changelog complet sur
    <a
      href="https://github.com/simongrossi/anonyfiles/commits/main"
      target="_blank"
      rel="noopener noreferrer"
      class="inline-flex items-center gap-1 text-brand-600 dark:text-brand-100 hover:underline"
    >
      <Github size={12} />
      GitHub
    </a>
    .
  </p>
</div>
