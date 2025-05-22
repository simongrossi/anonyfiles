// src/lib/anonymize.ts
import { invoke } from '@tauri-apps/api/tauri';

export async function anonymizeTextOrFile({ inputText, file, fileType, hasHeader }) {
  if (fileType === "txt" || !fileType) {
    return await invoke('anonymize_text', { text: inputText });
  }
  if (fileType === "csv" || fileType === "xlsx") {
    return await invoke('anonymize_file', {
      file,
      hasHeader
    });
  }
  throw new Error('Type de fichier non supporté');
}
