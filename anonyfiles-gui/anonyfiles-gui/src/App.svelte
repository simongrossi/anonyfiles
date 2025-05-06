<script lang="ts">
    // Importez votre composant DropZone
    import DropZone from './lib/DropZone.svelte';
    import { onMount, onDestroy } from 'svelte'; // <--- Importez les fonctions de cycle de vie
  
    // Fonction pour gérer les événements dragover et drop globaux
    // Cette fonction empêche le comportement par défaut du navigateur/système
    // qui pourrait ouvrir le fichier ou naviguer.
    function preventDefaultHandler(event: DragEvent) {
      event.preventDefault(); // Empêche le comportement par défaut (navigation, ouverture de fichier)
      // event.stopPropagation(); // Optionnel, pour arrêter la propagation, mais preventDefault est la clé ici
    }
  
    onMount(() => {
      // S'exécute lorsque le composant App.svelte est monté dans le DOM
  
      // Ajoute des écouteurs d'événements 'dragover' et 'drop' à l'objet 'window' entier.
      // Cela permet de s'assurer que le comportement par défaut est empêché quel que soit l'endroit
      // où l'événement commence à l'intérieur de la fenêtre.
      window.addEventListener('dragover', preventDefaultHandler as EventListener);
      window.addEventListener('drop', preventDefaultHandler as EventListener); // Empêche aussi le drop par défaut global
  
      console.log('Écouteurs de glisser-déposer globaux ajoutés sur window.');
  
      return () => {
        // Cette fonction de nettoyage s'exécute lorsque le composant App.svelte est détruit
        // Il est important de retirer les écouteurs ajoutés pour éviter les fuites de mémoire.
        window.removeEventListener('dragover', preventDefaultHandler as EventListener);
        window.removeEventListener('drop', preventDefaultHandler as EventListener);
  
        console.log('Écouteurs de glisser-déposer globaux retirés de window.');
      };
    });
  
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
      margin-bottom: 20px;
    }
  
    p {
        margin-top: 10px;
        color: #555;
    }
  
    /* Ajoutez ou ajustez d'autres styles si nécessaire */
  </style>