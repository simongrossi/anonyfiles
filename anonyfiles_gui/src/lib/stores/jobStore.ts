// anonyfiles_gui/src/lib/stores/jobStore.ts
import { writable } from 'svelte/store';

/**
 * Stocke l'ID du dernier job d'anonymisation ou de désanonymisation traité.
 * Mis à null s'il n'y a pas de job actif ou si le job a été supprimé.
 */
export const currentJobId = writable<string | null>(null);