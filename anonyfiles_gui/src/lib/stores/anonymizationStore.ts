// /path/to/your/anonyfiles_gui/src/lib/stores/anonymizationStore.ts
import { writable } from 'svelte/store';


export interface AuditLogEntry {
  pattern: string;
  replacement: string;
  type: string;
  count: number; 
}

export const inputText = writable('');
export const outputText = writable('');
export const auditLog = writable<AuditLogEntry[]>([]); // << TYPEZ VOTRE STORE ICI
export const mappingCSV = writable('');
export const isLoading = writable(false);
export const errorMessage = writable('');
export const inputLineCount = writable(0);
export const inputCharCount = writable(0);
export const outputLineCount = writable(0);
export const outputCharCount = writable(0);