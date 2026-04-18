// anonyfiles_gui/src/lib/utils/jobService.ts
import { writable } from 'svelte/store';
import { apiUrl, debugError } from './api';

export const notificationStore = writable<{ message: string, type: 'success' | 'error' } | null>(null);

export async function deleteJobFiles(jobId: string): Promise<boolean> {
    notificationStore.set(null);

    if (!jobId) {
        debugError("deleteJobFiles: jobId is required.");
        notificationStore.set({ message: "Aucun ID de job fourni pour la suppression.", type: 'error' });
        return false;
    }

    if (!window.confirm(`Êtes-vous sûr de vouloir supprimer tous les fichiers du job ${jobId} ? Cette action est irréversible.`)) {
        return false;
    }

    try {
        const response = await fetch(await apiUrl(`jobs/${jobId}`), {
            method: 'DELETE',
        });

        if (response.status === 204) {
            notificationStore.set({ message: `Job ${jobId} et ses fichiers supprimés avec succès.`, type: 'success' });
            return true;
        } else {
            let errorDetail = `Échec de la suppression du job ${jobId}.`;
            try {
                const errorData = await response.json();
                errorDetail = errorData.detail || `Erreur ${response.status}`;
            } catch {
                errorDetail = `Échec de la suppression du job ${jobId}. Statut: ${response.status}`;
            }
            notificationStore.set({ message: errorDetail, type: 'error' });
            debugError(errorDetail);
            return false;
        }
    } catch (err: any) {
        const errorMessage = err.message || "Une erreur réseau est survenue lors de la tentative de suppression du job.";
        notificationStore.set({ message: errorMessage, type: 'error' });
        debugError(`Error deleting job ${jobId}:`, err);
        return false;
    }
}