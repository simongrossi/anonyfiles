<script lang="ts">
    // Variable pour gérer l'état visuel (quand un élément est glissé au-dessus)
    let isDragging = false;
  
    // Fonction appelée lorsqu'un élément est glissé au-dessus de la zone
    // NOTE : L'annotation de type ': DragEvent' a été retirée pour résoudre l'erreur de compilation.
    function handleDragOver(event) {
      event.preventDefault(); // Empêche le comportement par défaut du navigateur (ouvrir le fichier)
      isDragging = true;
      // Optionnel: ajouter dataTransfer.dropEffect pour indiquer le type d'opération
      // event.dataTransfer.dropEffect = 'copy';
    }
  
    // Fonction appelée lorsqu'un élément quitte la zone de glisser-déposer
    // NOTE : L'annotation de type ': DragEvent' a été retirée.
    function handleDragLeave(event) {
      event.preventDefault();
      isDragging = false;
    }
  
    // Fonction appelée lorsqu'un élément est déposé dans la zone
    // NOTE : L'annotation de type ': DragEvent' a été retirée.
    function handleDrop(event) {
      event.preventDefault();
      isDragging = false; // Retour à l'état normal après le dépôt
  
      // Récupérer la liste des fichiers déposés
      const files = event.dataTransfer?.files;
  
      if (files && files.length > 0) {
        console.log("Fichiers déposés :");
        // Ici, nous affichons juste les noms et types des fichiers déposés dans la console
        for (let i = 0; i < files.length; i++) {
          console.log(`- Nom : ${files[i].name}, Type : ${files[i].type}`);
        }
  
        // Prochaine étape : utiliser l'API Tauri pour obtenir les chemins complets des fichiers
        // et les envoyer au backend.
      }
    }
  </script>
  
  <div
    class="drop-zone"
    class:dragging={isDragging}
    on:dragover={handleDragOver}
    on:dragleave={handleDragLeave}
    on:drop={handleDrop}
  >
    {#if isDragging}
      <p>Relâchez les fichiers ici</p>
    {:else}
      <p>Glissez vos fichiers ici pour les anonymiser</p>
    {/if}
  </div>
  
  <style>
    .drop-zone {
      border: 2px dashed #ccc;
      border-radius: 10px;
      padding: 20px;
      text-align: center;
      cursor: pointer;
      transition: border-color 0.3s ease, background-color 0.3s ease; /* Ajout transition background */
      margin-top: 20px; /* Juste pour l'espacement */
      width: 80%; /* Exemple: prend 80% de la largeur du conteneur parent */
      max-width: 400px; /* Largeur maximale */
      box-sizing: border-box; /* Inclure padding et border dans la largeur */
    }
  
    .drop-zone.dragging {
      border-color: #007bff; /* Couleur différente quand on glisse au-dessus */
      background-color: #e9f5ff; /* Fond différent */
    }
  
    /* Styles pour la zone quand elle n'est pas active ou glissée */
    .drop-zone p {
      margin: 0;
      color: #555;
      user-select: none; /* Empêche la sélection du texte */
    }
  
    .drop-zone.dragging p {
      color: #007bff;
    }
  </style>