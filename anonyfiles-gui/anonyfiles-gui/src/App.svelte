<script lang="ts">
  // ... autres imports si vous en avez déjà
  import DropZone from './lib/DropZone.svelte'; // Importez le nouveau composant
</script>

<main class="container">
  <h1>Anonyfiles GUI</h1>

  <DropZone />

  <p>
    <br>
    Cliquez sur les logos pour en savoir plus sur les technologies utilisées :
  </p>

  <div class="row">
    <a href="https://vitejs.dev" target="_blank">
      <img src="/src/assets/vite.svg" class="logo vite" alt="Vite logo" />
    </a>
    <a href="https://tauri.app" target="_blank">
      <img src="/src/assets/tauri.svg" class="logo tauri" alt="Tauri logo" />
    </a>
    <a href="https://svelte.dev" target="_blank"> <img src="/src/assets/svelte.svg" class="logo svelte" alt="Svelte logo" />
    </a>
  </div>

  <p>En phase de test</p>


  </main>

<style>
  /* Conservez les styles de base de votre application, ajustez si nécessaire */
  .container {
    margin: 0;
    padding-top: 5vh; /* Ajustez l'espace en haut */
    display: flex;
    flex-direction: column;
    /* center items horizontally */
    align-items: center;
    text-align: center;
  }

  .logo {
    height: 6em;
    padding: 1.5em;
    will-change: filter;
    transition: filter 0.75s;
  }

  .logo:hover {
    filter: drop-shadow(0 0 2em #646cffaa);
  }

  .logo.tauri:hover {
    filter: drop-shadow(0 0 2em #24c8db);
  }

  .logo.svelte:hover { /* Ajoutez un style pour le logo Svelte si vous l'ajoutez */
     filter: drop-shadow(0 0 2em #ff3e00aa);
  }


  .row {
    display: flex;
    justify-content: center;
  }

  h1 {
    text-align: center;
    color: #333; /* Couleur de titre plus sombre */
  }

  /* Ajoutez ou ajustez d'autres styles si nécessaire */
</style>