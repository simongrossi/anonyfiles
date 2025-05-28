// #anonyfiles/anonyfiles_gui/src/lib/stores/anonymizationStore.ts
import { writable } from 'svelte/store';

export const inputText = writable('');
export const outputText = writable('');
export const auditLog = writable([]);
export const mappingCSV = writable('');
export const isLoading = writable(false);
export const errorMessage = writable('');
