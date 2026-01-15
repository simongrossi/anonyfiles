// #anonyfiles/anonyfiles_gui/src/lib/utils/anonymize.ts
import { get } from 'svelte/store';
import {
  inputText,
  outputText,
  auditLog,
  mappingCSV,
  isLoading,
  errorMessage,
  outputLineCount,
  outputCharCount
} from '../stores/anonymizationStore';
import { currentJobId } from '$lib/stores/jobStore';

interface RunAnonymizationParams {
  fileType?: string;
  fileName?: string;
  hasHeader?: boolean;
  xlsxFile?: File | null;
  selected: Record<string, boolean>;
  customReplacementRules?: { pattern: string; replacement: string; isRegex?: boolean }[];
}

function isTauri() {
  return !!(window && '__TAURI_IPC__' in window);
}

export async function runAnonymization({
  fileType,
  fileName,
  hasHeader,
  xlsxFile,
  selected,
  customReplacementRules
}: RunAnonymizationParams) {
  isLoading.set(true);
  errorMessage.set('');
  outputText.set('');
  outputLineCount.set(0);
  outputCharCount.set(0);
  auditLog.set([]);
  mappingCSV.set('');
  currentJobId.set(null);

  try {
    if (isTauri()) {
      throw new Error("Tauri non supporté en mode web !");
    } else {
      const API_URL = '/api';

      let formData = new FormData();

      if (fileType === "txt" || !fileType) {
        formData.append('file', new Blob([get(inputText)], { type: 'text/plain' }), fileName || 'input.txt');
      } else if (fileType === "csv" || fileType === "xlsx") {
        if (!xlsxFile) throw new Error("Fichier manquant pour le type xlsx/csv");
        formData.append('file', xlsxFile, fileName);
        formData.append('has_header', String(!!hasHeader));
      }

      formData.append('config_options', JSON.stringify(selected));

      if (customReplacementRules && customReplacementRules.length > 0) {
        console.log("runAnonymization - règles personnalisées envoyées :", customReplacementRules);
        formData.append('custom_replacement_rules', JSON.stringify(customReplacementRules));
      }

      formData.append('file_type', fileType || '');

      const response = await fetch(`${API_URL}/anonymize/`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errMsg = await response.text();
        console.error("Erreur API (anonymize):", errMsg);
        try {
          const errJson = JSON.parse(errMsg);
          throw new Error(`[${response.status}] Erreur backend: ${errJson.detail || errMsg}`);
        } catch (e) {
          throw new Error(`[${response.status}] Erreur backend: ${errMsg}`);
        }
      }

      const data = await response.json();

      if (data.job_id) {
        currentJobId.set(data.job_id);
        let polling = true;
        while (polling) {
          await new Promise(r => setTimeout(r, 1200));
          const pollResp = await fetch(`${API_URL}/anonymize_status/${data.job_id}`);

          if (!pollResp.ok) {
            const pollErrText = await pollResp.text();
            console.error("Erreur API (anonymize_status):", pollErrText);
            let specificError = `Erreur lors du polling du statut (HTTP ${pollResp.status}).`;
            try {
              const pollErrJson = JSON.parse(pollErrText);
              specificError = pollErrJson.detail || specificError;
            } catch (e) { }
            errorMessage.set(specificError);
            polling = false;
            continue;
          }

          const pollData = await pollResp.json();

          if (pollData.status === "finished") {
            const currentOutputText = pollData.anonymized_text || '';
            outputText.set(currentOutputText);
            outputCharCount.set(currentOutputText.length);
            outputLineCount.set(currentOutputText.split('\n').length);
            auditLog.set(pollData.audit_log || []);
            mappingCSV.set(pollData.mapping_csv || '');
            polling = false;
          } else if (pollData.status === "error") {
            errorMessage.set(pollData.error || "Erreur inconnue lors du polling de l'anonymisation.");
            polling = false;
          } else if (pollData.status === "pending") {
            console.log("Job status pending for:", data.job_id);
          } else {
            errorMessage.set(`Statut de job inattendu: ${pollData.status}`);
            polling = false;
          }
        }
      } else {
        const directOutputText = data.outputText || data.anonymized_text || '';
        outputText.set(directOutputText);
        outputCharCount.set(directOutputText.length);
        outputLineCount.set(directOutputText.split('\n').length);
        auditLog.set(data.auditLog || data.audit_log || []);
        mappingCSV.set(data.mappingCSV || data.mapping_csv || '');
        currentJobId.set(null);
      }
    }
  } catch (err: any) {
    errorMessage.set(err?.message || 'Erreur lors de l\'anonymisation');
    currentJobId.set(null);
  } finally {
    isLoading.set(false);
  }
}
