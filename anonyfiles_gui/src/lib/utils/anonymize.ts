// #anonyfiles/anonyfiles_gui/src/lib/utils/anonymize.ts
import { get } from 'svelte/store';
import { inputText, outputText, auditLog, mappingCSV, isLoading, errorMessage } from '../stores/anonymizationStore';

function isTauri() {
  return !!(window && '__TAURI_IPC__' in window);
}

export async function runAnonymization({ fileType, fileName, hasHeader, xlsxFile, selected, customReplacementRules }) {
  isLoading.set(true);
  errorMessage.set('');
  outputText.set('');
  auditLog.set([]);
  mappingCSV.set('');

  try {
    if (isTauri()) {
      throw new Error("Tauri non supporté en mode web !");
    } else {
      const API_URL = import.meta.env.VITE_ANONYFILES_API_URL || 'http://127.0.0.1:8000/api';

      let formData = new FormData();
      if (fileType === "txt" || !fileType) {
        formData.append('file', new Blob([get(inputText)], { type: 'text/plain' }), fileName || 'input.txt');
      } else if (fileType === "csv" || fileType === "xlsx") {
        if (!xlsxFile) throw new Error("Fichier manquant pour le type xlsx/csv");
        formData.append('file', xlsxFile, fileName);
        formData.append('has_header', String(!!hasHeader));
      }
      formData.append('config_options', JSON.stringify({ ...selected, customReplacementRules }));
      formData.append('file_type', fileType);

      const response = await fetch(`${API_URL}/anonymize/`, {
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
          await new Promise(r => setTimeout(r, 1200));
          const pollResp = await fetch(`${API_URL}/anonymize_status/${data.job_id}`);
          const pollData = await pollResp.json();

          if (pollData.status === "finished") {
            outputText.set(pollData.anonymized_text || '');
            auditLog.set(pollData.audit_log || []);
            mappingCSV.set(pollData.mapping_csv || '');
            polling = false;
          } else if (pollData.status === "error") {
            throw new Error(pollData.error || "Erreur inconnue lors du polling.");
          }
        }
      } else {
        outputText.set(data.outputText || data.anonymized_text || '');
        auditLog.set(data.auditLog || data.audit_log || []);
        mappingCSV.set(data.mappingCSV || data.mapping_csv || '');
      }
    }
  } catch (err: any) {
    errorMessage.set(err?.message || 'Erreur lors de l\'anonymisation');
  } finally {
    isLoading.set(false);
  }
}
