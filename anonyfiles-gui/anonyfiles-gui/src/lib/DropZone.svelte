<script lang="ts">
    import { open } from '@tauri-apps/plugin-dialog'; // <--- Importez la fonction open
  
    let isDragging = false;
  
    function handleDragOver(event: DragEvent) { // Vous pouvez remettre DragEvent si ça ne cause pas d'erreur maintenant
      event.preventDefault();
      isDragging = true;
    }
  
    function handleDragLeave(event: DragEvent) { // Remettre DragEvent ici aussi si vous voulez
      event.preventDefault();
      isDragging = false;
    }
  
    async function handleDrop(event: DragEvent) { // Et ici
      event.preventDefault();
      isDragging = false;
  
      const files = event.dataTransfer?.files;
  
      if (files && files.length > 0) {
        console.log("Fichiers déposés :");
        // Nous afficherons ici les chemins complets plus tard, via l'API Tauri
        for (let i = 0; i < files.length; i++) {
          console.log(`- Nom : ${files[i].name}, Type : ${files[i].type}`);
        }
  
        // Prochaine étape: Traiter les fichiers déposés (obtenir les chemins réels et les envoyer au backend)
        // Nous devrons obtenir les chemins via l'API Tauri pour les fichiers déposés.
      }
    }
  
    // <--- Nouvelle fonction pour gérer le clic
    async function openFileSelection() {
      try {
        // Ouvre une boîte de dialogue pour sélectionner des fichiers
        // 'multiple: true' permet de sélectionner plusieurs fichiers
        // 'filters' peut être utilisé pour limiter les types de fichiers (optionnel)
        const selected = await open({
          multiple: true,
          title: 'Sélectionner les fichiers à anonymiser',
          // Exemple de filtre pour les documents (ajustez selon les formats supportés)
          filters: [{
            name: 'Documents',
            extensions: ['docx', 'xlsx', 'csv', 'txt']
          }]
        });
  
        if (Array.isArray(selected)) {
          // L'utilisateur a sélectionné un ou plusieurs fichiers
          console.log("Fichiers sélectionnés via la boîte de dialogue :");
          selected.forEach(filePath => console.log(`- Chemin : ${filePath}`));
          // Prochaine étape : Traiter les fichiers sélectionnés (envoyer les chemins au backend)
  
        } else if (selected === null) {
          // L'utilisateur a annulé la sélection
          console.log("Sélection de fichier annulée.");
        } else {
          // L'utilisateur a sélectionné un seul fichier (si multiple: false)
          console.log("Fichier sélectionné via la boîte de dialogue :", selected);
          // Prochaine étape : Traiter le fichier sélectionné (envoyer le chemin au backend)
        }
      } catch (error) {
        console.error("Erreur lors de l'ouverture de la boîte de dialogue :", error);
      }
    }
    // Fin nouvelle fonction
  </script>
  
  <div
    class="drop-zone"
    class:dragging={isDragging}
    on:dragover={handleDragOver}
    on:dragleave={handleDragLeave}
    on:drop={handleDrop}
    on:click={openFileSelection} // <--- Ajoutez cet écouteur
  >
    {#if isDragging}
      <p>Relâchez les fichiers ici</p>
    {:else}
      <p>Glissez vos fichiers ici ou cliquez pour sélectionner</p> {/if}
  </div>
  
  <style>
    .drop-zone {
      border: 2px dashed #ccc;
      border-radius: 10px;
      padding: 20px;
      text-align: center;
      cursor: pointer;
      transition: border-color 0.3s ease, background-color 0.3s ease;
      margin-top: 20px;
      width: 80%;
      max-width: 400px;
      box-sizing: border-box;
    }
  
    .drop-zone.dragging {
      border-color: #007bff;
      background-color: #e9f5ff;
    }
  
    .drop-zone p {
      margin: 0;
      color: #555;
      user-select: none;
    }
  
    .drop-zone.dragging p {
      color: #007bff;
    }
  </style>