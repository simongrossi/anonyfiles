// Exemple pour src/lib/utils/deanonymize.ts (à créer ou adapter)
import { get } from 'svelte/store';
import {
    fileToDeanonymize, // Store pour le fichier à désanonymiser
    mappingFile,       // Store pour le fichier de mapping
    isDeanonymizing,
    deanonymizedText,
    deanonymizationError
} from '$lib/stores/deanonymizationStore'; // Ajustez le chemin

export async function runDeanonymization(permissive: boolean = false) {
    const currentFileToDeanonymize = get(fileToDeanonymize);
    const currentMappingFile = get(mappingFile);

    if (!currentFileToDeanonymize || !currentMappingFile) {
        deanonymizationError.set('Veuillez sélectionner le fichier à désanonymiser ET le fichier de mapping.');
        return;
    }

    isDeanonymizing.set(true);
    deanonymizationError.set('');
    deanonymizedText.set('');

    try {
        const API_URL = import.meta.env.VITE_ANONYFILES_API_URL || 'http://127.0.0.1:8000/api';

        const formData = new FormData();
        formData.append('file', currentFileToDeanonymize);
        formData.append('mapping', currentMappingFile);
        formData.append('permissive', String(permissive));

        const response = await fetch(`${API_URL}/api/deanonymize/`, { // Notez le double /api/ si votre API est structurée ainsi
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const errMsg = await response.text();
            throw new Error(`[${response.status}] Erreur backend: ${errMsg}`);
        }

        const data = await response.json();

        if (data.job_id) {
            let polling = true;
            while (polling) {
                await new Promise(r => setTimeout(r, 1200)); // Attente entre les polls
                // L'URL pour le statut de désanonymisation doit être /api/deanonymize_status/{job_id}
                const pollResp = await fetch(`<span class="math-inline">\{API\_URL\}/api/deanonymize\_status/</span>{data.job_id}`);
                const pollData = await pollResp.json();

                if (pollData.status === "finished") {
                    deanonymizedText.set(pollData.deanonymized_text || '');
                    // Vous pouvez aussi stocker pollData.report et pollData.audit_log si nécessaire
                    polling = false;
                } else if (pollData.status === "error") {
                    throw new Error(pollData.error || "Erreur inconnue lors du polling de désanonymisation.");
                }
            }
        } else {
             // Gestion d'une réponse directe (si l'API ne fait pas de polling)
            deanonymizedText.set(data.deanonymized_text || '');
        }

    } catch (err: any) {
        deanonymizationError.set(err?.message || 'Erreur lors de la désanonymisation.');
    } finally {
        isDeanonymizing.set(false);
    }
}