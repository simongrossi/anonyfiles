<script lang="ts">
  import DataAnonymizer from './lib/DataAnonymizer.svelte';
  import DeAnonymizer from './lib/DeAnonymizer.svelte';
  import ConfigurationView from './lib/ConfigurationView.svelte';
  import AuditLogTable from './lib/AuditLogTable.svelte';

  let tab = 'anonymizer';
  const tabs = [
    { key: 'anonymizer', icon: '🕵️', label: 'Anonymisation' },
    { key: 'deanonymizer', icon: '🔓', label: 'Désanonymisation' },
    { key: 'log', icon: '📜', label: 'Log' },
    { key: 'config', icon: '⚙️', label: 'Configuration' }
  ];

  // Etat global pour l'anonymisation
  let lastInput = "";
  let lastOutput = "";
  let lastAuditLog = [];

  function handleAnonymizationComplete(event) {
    // On conserve l'état même si on change d'onglet
    lastInput = event.detail.inputText;
    lastOutput = event.detail.outputText;
    lastAuditLog = event.detail.auditLog;
    // tab = 'log'; // Décommente pour basculer auto sur log
  }

  function handleReset() {
    lastInput = "";
    lastOutput = "";
    lastAuditLog = [];
  }
</script>

<div class="flex h-screen">
  <nav class="w-56 bg-gray-800 text-white flex flex-col py-6 shadow-lg gap-2">
    {#each tabs as t}
      <button
        class="flex items-center gap-2 px-6 py-3 text-lg font-semibold text-left hover:bg-gray-700 transition rounded-xl focus:outline-none {tab === t.key ? 'bg-gray-700' : ''}"
        on:click={() => tab = t.key}
      >
        <span>{t.icon}</span>
        {t.label}
      </button>
    {/each}
    <div class="flex-grow"></div>
    <a
      href="https://github.com/simongrossi/anonyfiles"
      class="flex items-center justify-center mb-2 p-2 rounded-xl hover:bg-gray-700 transition"
      target="_blank"
      rel="noopener noreferrer"
      aria-label="Voir le projet sur GitHub"
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-7 h-7">
        <path d="M12 2C6.48 2 2 6.58 2 12.26c0 4.5 2.87 8.31 6.84 9.66.5.09.68-.22.68-.48 0-.24-.01-.87-.01-1.7-2.78.62-3.37-1.36-3.37-1.36-.45-1.18-1.11-1.5-1.11-1.5-.91-.64.07-.63.07-.63 1.01.07 1.54 1.06 1.54 1.06 .89 1.56 2.34 1.11 2.91.85.09-.66.35-1.11.63-1.37-2.22-.26-4.56-1.14-4.56-5.06 0-1.12.39-2.04 1.02-2.76-.1-.26-.45-1.31.1-2.73 0 0 .84-.28 2.75 1.05a9.25 9.25 0 0 1 5 0c1.91-1.33 2.75-1.05 2.75-1.05 .55 1.42.2 2.47.1 2.73 .63.72 1.02 1.64 1.02 2.76 0 3.93-2.34 4.8-4.57 5.05.36.31.68.92.68 1.86 0 1.35-.01 2.43-.01 2.76 0 .27.18.58.69.48A10.02 10.02 0 0 0 22 12.26C22 6.58 17.52 2 12 2z"/>
      </svg>
    </a>
  </nav>
  <main class="flex-1 bg-gray-50 dark:bg-gray-900 transition-colors overflow-y-auto">
    <div class="mx-auto max-w-4xl px-4 py-8">
      {#if tab === 'anonymizer'}
        <DataAnonymizer
          inputText={lastInput}
          outputText={lastOutput}
          auditLog={lastAuditLog}
          on:anonymizationComplete={handleAnonymizationComplete}
          on:resetRequested={handleReset}
        />
      {:else if tab === 'deanonymizer'}
        <DeAnonymizer />
      {:else if tab === 'log'}
        <AuditLogTable auditLog={lastAuditLog} />
      {:else if tab === 'config'}
        <ConfigurationView />
      {/if}
    </div>
  </main>
</div>
