// anonyfiles_gui/src/lib/utils/jobService.ts
import { writable } from 'svelte/store';

export const notificationStore = writable<{ message: string, type: 'success' | 'error' } | null>(null);

export async function deleteJobFiles(jobId: string): Promise<boolean> {
    // Utiliser la même convention que pour API_URL dans anonymize.ts
    // VITE_ANONYFILES_API_URL devrait être "http://<host>:<port>/api"
    // ou la valeur par défaut "http://127.0.0.1:8000/api"
    const API_URL_WITH_PREFIX = import.meta.env.VITE_ANONYFILES_API_URL || 'http://127.0.0.1:8000/api';
    
    notificationStore.set(null); 

    if (!jobId) {
        console.error("deleteJobFiles: jobId is required.");
        notificationStore.set({ message: "Aucun ID de job fourni pour la suppression.", type: 'error' });
        return false;
    }

    if (!window.confirm(`Êtes-vous sûr de vouloir supprimer tous les fichiers du job ${jobId} ? Cette action est irréversible.`)) {
        return false;
    }

    try {
        // Construire l'URL : API_URL_WITH_PREFIX est la base (ex: http://localhost:8000/api)
        // et on ajoute le chemin spécifique de l'endpoint (ex: /jobs/jobId)
        const response = await fetch(`${API_URL_WITH_PREFIX}/jobs/${jobId}`, { 
            method: 'DELETE',
        });

        if (response.status === 204) { 
            notificationStore.set({ message: `Job ${jobId} et ses fichiers supprimés avec succès.`, type: 'success' });
            return true;
        } else {
            let errorDetail = `Échec de la suppression du job ${jobId}.`;
            try {
                // Si l'API renvoie un JSON d'erreur (par exemple, pour un 404 ou 500 bien géré par FastAPI)
                const errorData = await response.json();
                errorDetail = errorData.detail || `Erreur ${response.status}`;
            } catch (e) {
                // Si la réponse n'est pas du JSON (par exemple, une page HTML pour un 404 brut)
                errorDetail = `Échec de la suppression du job ${jobId}. Statut: ${response.status}`;
            }
            notificationStore.set({ message: errorDetail, type: 'error' });
            console.error(errorDetail);
            return false;
        }
    } catch (err: any) {
        const errorMessage = err.message || "Une erreur réseau est survenue lors de la tentative de suppression du job.";
        notificationStore.set({ message: errorMessage, type: 'error' });
        console.error(`Error deleting job ${jobId}:`, err);
        return false;
    }
}