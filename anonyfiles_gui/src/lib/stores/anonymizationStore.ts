// /path/to/your/anonyfiles_gui/src/lib/stores/anonymizationStore.ts
import { writable } from 'svelte/store';


export interface AuditLogEntry {
  pattern: string;
  replacement: string;
  type: string;
  count: number; 
}

export interface PrivacyWarning {
  kind: string;
  label: string;
  count: number;
  examples: string[];
  severity: 'high' | 'medium' | 'low' | string;
  message: string;
}

export const inputText = writable('');
export const outputText = writable('');
export const auditLog = writable<AuditLogEntry[]>([]); // << TYPEZ VOTRE STORE ICI
export const mappingCSV = writable('');
export const privacyWarnings = writable<PrivacyWarning[]>([]);
export const isLoading = writable(false);
export const errorMessage = writable('');
export const inputLineCount = writable(0);
export const inputCharCount = writable(0);
export const outputLineCount = writable(0);
export const outputCharCount = writable(0);
/** Nom du fichier de sortie produit par le backend (vide si aucun). */
export const outputFileName = writable('');
/**
 * `true` quand la sortie est un fichier binaire (.docx, .pdf, .xlsx) : il n'y a
 * pas d'aperçu texte, seul le téléchargement du fichier est possible.
 */
export const outputIsBinary = writable(false);
