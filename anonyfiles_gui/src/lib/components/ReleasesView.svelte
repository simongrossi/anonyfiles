<!-- #anonyfiles/anonyfiles_gui/src/lib/components/ReleasesView.svelte -->
<script lang="ts">
  // Pas besoin de chargement dynamique ici : changelog intégré statiquement
</script>

<div class="space-y-6">
  <h2 class="text-3xl font-bold text-gray-800 dark:text-white">Nouveautés & Mises à jour</h2>

  <div class="p-4 bg-white dark:bg-gray-800 rounded-lg shadow space-y-4">
    <h3 class="text-xl font-semibold text-gray-700 dark:text-gray-200">Résumé des évolutions</h3>
    <p class="text-gray-600 dark:text-gray-400">
      Voici un condensé chronologique des principales fonctionnalités et améliorations apportées au projet <strong>Anonyfiles</strong> :
    </p>

    <ul class="list-disc list-inside text-gray-600 dark:text-gray-400 space-y-1">
      <li><strong>Démarrage du projet</strong> avec anonymisation texte simple (.txt), configuration YAML, moteur basé sur spaCy et remplacement basique.</li>
      <li>Ajout progressif du <strong>support multi-format</strong> : .csv avec en-têtes, .docx, .xlsx, puis .pdf et .json, avec prévisualisation intégrée.</li>
      <li>Introduction des <strong>règles personnalisées</strong> (simples ou regex), priorisées sur les entités spaCy.</li>
      <li>Mise en place d’un système <strong>d’audit complet</strong> (mapping CSV, journal de traitement, fichier log horodaté).</li>
      <li>Ajout d’un <strong>système de désanonymisation</strong> basé sur le fichier de mapping CSV exportable.</li>
      <li>Refactorisation du moteur : centralisation des traitements, meilleure robustesse, séparation claire logique/analyse/remplacement.</li>
      <li>Ajout de l’<strong>interface graphique</strong> (Tauri + Svelte) avec drag & drop, preview dynamique, affichage avant/après et responsive design.</li>
      <li>Implémentation de l’<strong>API FastAPI</strong> avec endpoints d’anonymisation, suivi de statut, téléchargement de fichiers et logs intégrés.</li>
      <li>Ajout d’une route <code>DELETE /api/jobs/&lt;id&gt;</code> pour <strong>supprimer les jobs</strong> obsolètes (avec intégration dans la GUI).</li>
      <li>Amélioration de l’<strong>ergonomie desktop</strong> : refonte du layout, header fixe avec logo centré, sidebar compacte en mobile, suppression des doublons visuels.</li>
      <li>Gestion dynamique des <strong>règles personnalisées</strong> dans l’interface, avec export/import JSON, détection de doublons, etc.</li>
      <li>Modernisation du <strong>design global</strong> : toggles responsives, champs épurés, conteneurs adaptatifs, refonte du composant de dépôt de fichiers.</li>
      <li>Améliorations backend et frontend continues : nettoyage, contrôle d’erreurs, affichage conditionnel, gestion des messages, refactors TypeScript/Svelte.</li>
    </ul>

    <p class="text-gray-600 dark:text-gray-400 pt-2">
      Ce résumé reflète l'évolution du projet vers une solution complète, stable et modulaire, adaptée à de multiples cas d’usage (RGPD, pseudonymisation, audit, transmission de fichiers sensibles…).
    </p>
  </div>

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
