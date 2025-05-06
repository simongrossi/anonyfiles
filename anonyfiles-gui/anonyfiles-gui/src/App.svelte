<script lang="ts">
    // Importez votre composant DropZone
    import DropZone from './lib/DropZone.svelte';
  
    // Note : Les fonctions handleDragOver et handleDrop que nous avions ici initialement
    // pour la gestion globale ne sont plus nécessaires car nous utilisons
    // directement les modificateurs d'événements de Svelte sur la balise <main>.
    // Le composant DropZone gère ses propres événements locaux.
  
  </script>
  
  <main
    class="container"
    on:dragover|preventDefault|stopPropagation
    on:drop|preventDefault|stopPropagation
  >
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
      <a href="https://svelte.dev" target="_blank">
         <img src="/src/assets/svelte.svg" class="logo svelte" alt="Svelte logo" />
      </a>
    </div>
  
    <p>En phase de test</p>
  
    </main>
  
  <style>
    .container {
      margin: 0;
      padding-top: 5vh; /* Ajustez l'espace en haut */
      display: flex;
      flex-direction: column;
      /* center items horizontally */
      align-items: center;
      text-align: center;
      /* Ajoutez min-height pour que la zone de dépôt puisse recevoir le drop si le contenu est court */
      min-height: 100vh; /* Occupe au moins toute la hauteur de la fenêtre */
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
  
    .logo.svelte:hover {
       filter: drop-shadow(0 0 2em #ff3e00aa);
    }
  
  
    .row {
      display: flex;
      justify-content: center;
      margin-top: 20px; /* Ajoute un peu d'espace au-dessus des logos */
    }
  
    h1 {
      text-align: center;
      color: #333;
      margin-bottom: 20px; /* Ajoute un peu d'espace sous le titre */
    }
  
    p {
        margin-top: 10px;
        color: #555;
    }
  
    /* Ajoutez ou ajustez d'autres styles si nécessaire */
  </style>