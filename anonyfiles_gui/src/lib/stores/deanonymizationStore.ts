// src/lib/stores/deanonymizationStore.ts
import { writable } from 'svelte/store';

export const fileToDeanonymize = writable<File | null>(null);
export const mappingFile = writable<File | null>(null);
export const isDeanonymizing = writable<boolean>(false);
export const deanonymizedText = writable<string>('');
export const deanonymizationError = writable<string>('');