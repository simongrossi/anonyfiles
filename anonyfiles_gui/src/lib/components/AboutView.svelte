<script lang="ts">
  import { Info, Sparkles, Github, Wrench } from 'lucide-svelte';
</script>

<div class="w-full max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 pb-10">
  <div class="mb-5 flex items-center gap-3">
    <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 dark:bg-brand-900/30 text-brand-600 dark:text-brand-100">
      <Info size={20} />
    </div>
    <div>
      <h1 class="text-lg font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
        À propos d'Anonyfiles
      </h1>
      <p class="text-xs text-zinc-500 dark:text-zinc-400">
        Qu'est-ce que c'est et pourquoi ça existe.
      </p>
    </div>
  </div>

  <section class="ui-section mb-5">
    <header class="ui-section-header">
      <Sparkles size={16} class="text-zinc-400 dark:text-zinc-500" />
      <span class="ui-section-title">Pourquoi ce projet ?</span>
    </header>
    <div class="ui-section-body prose prose-sm dark:prose-invert max-w-none">
      <p>
        Anonyfiles est né d'un besoin simple : anonymiser rapidement des fichiers texte sans
        ouvrir Excel, Notepad++ ou écrire des scripts à la main.
      </p>
      <p>
        En manipulant régulièrement des documents contenant des données sensibles (notamment
        pour des requêtes à des IA), je me suis rendu compte qu'il n'existait pas vraiment
        d'outil léger, fiable et personnalisable pour faire ça facilement. J'ai donc décidé
        de créer ma propre solution.
      </p>
    </div>
  </section>

  <section class="ui-section mb-5">
    <header class="ui-section-header">
      <Wrench size={16} class="text-zinc-400 dark:text-zinc-500" />
      <span class="ui-section-title">Ce que fait Anonyfiles</span>
    </header>
    <div class="ui-section-body">
      <ul class="space-y-2 text-sm text-zinc-700 dark:text-zinc-200">
        {#each [
          'Anonymisation automatique de fichiers texte (.txt, .csv, .json, .docx, etc.).',
          'Suppression ou remplacement des noms, emails, adresses, IBAN, etc.',
          'Personnalisation possible avec vos propres règles de remplacement.',
          'Journalisation complète pour garder une trace des modifications.',
          'Possibilité de désanonymiser un fichier si la correspondance a été conservée.',
        ] as bullet}
          <li class="flex items-start gap-2">
            <span class="mt-2 h-1 w-1 rounded-full bg-brand-500 shrink-0"></span>
            <span>{bullet}</span>
          </li>
        {/each}
      </ul>
    </div>
  </section>

  <div class="flex flex-col items-center gap-2 mt-8 text-center text-xs text-zinc-500 dark:text-zinc-400">
    <span>Anonyfiles — <span class="ui-badge-brand">v1.2.0</span></span>
    <span>
      Développé par Simon Grossi ·
      <a
        href="https://github.com/simongrossi/anonyfiles"
        target="_blank"
        rel="noopener noreferrer"
        class="inline-flex items-center gap-1 text-brand-600 dark:text-brand-100 hover:underline"
      >
        <Github size={12} />
        Code source
      </a>
    </span>
  </div>
</div>
