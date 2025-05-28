import { writable } from 'svelte/store';

export const inputFile = writable<File | null>(null);
export const inputText = writable<string>('');
export const outputText = writable<string>('');
export const mappingCSV = writable<string>('');
export const auditLog = writable<any[]>([]);
export const isLoading = writable<boolean>(false);
export const errorMessage = writable<string>('');
