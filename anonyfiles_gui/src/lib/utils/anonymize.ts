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
  outputCharCount,
  type AuditLogEntry
} from '../stores/anonymizationStore';
import { currentJobId } from '$lib/stores/jobStore';
import { apiUrl, pollJob, debug, debugError } from './api';

interface RunAnonymizationParams {
  fileType?: string;
  fileName?: string;
  hasHeader?: boolean;
  xlsxFile?: File | null;
  selected: Record<string, boolean>;
  customReplacementRules?: { pattern: string; replacement: string; isRegex?: boolean }[];
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
    const formData = new FormData();

    if (fileType === 'txt' || !fileType) {
      formData.append('file', new Blob([get(inputText)], { type: 'text/plain' }), fileName || 'input.txt');
    } else if (fileType === 'csv' || fileType === 'xlsx') {
      if (!xlsxFile) throw new Error('Fichier manquant pour le type xlsx/csv');
      formData.append('file', xlsxFile, fileName);
      formData.append('has_header', String(!!hasHeader));
    }

    formData.append('config_options', JSON.stringify(selected));

    if (customReplacementRules && customReplacementRules.length > 0) {
      debug('runAnonymization - règles personnalisées envoyées :', customReplacementRules);
      formData.append('custom_replacement_rules', JSON.stringify(customReplacementRules));
    }

    formData.append('file_type', fileType || '');

    const response = await fetch(await apiUrl('anonymize/'), {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errMsg = await response.text();
      debugError('Erreur API (anonymize):', errMsg);
      try {
        const errJson = JSON.parse(errMsg);
        throw new Error(`[${response.status}] Erreur backend: ${errJson.detail || errMsg}`);
      } catch {
        throw new Error(`[${response.status}] Erreur backend: ${errMsg}`);
      }
    }

    const data = await response.json();

    if (data.job_id) {
      currentJobId.set(data.job_id);
      const pollData = await pollJob<{
        status: string;
        anonymized_text?: string;
        audit_log?: AuditLogEntry[];
        mapping_csv?: string;
        error?: string;
      }>(await apiUrl(`anonymize_status/${data.job_id}`));

      const currentOutputText = pollData.anonymized_text || '';
      outputText.set(currentOutputText);
      outputCharCount.set(currentOutputText.length);
      outputLineCount.set(currentOutputText.split('\n').length);
      auditLog.set(pollData.audit_log || []);
      mappingCSV.set(pollData.mapping_csv || '');
    } else {
      const directOutputText = data.outputText || data.anonymized_text || '';
      outputText.set(directOutputText);
      outputCharCount.set(directOutputText.length);
      outputLineCount.set(directOutputText.split('\n').length);
      auditLog.set(data.auditLog || data.audit_log || []);
      mappingCSV.set(data.mappingCSV || data.mapping_csv || '');
      currentJobId.set(null);
    }
  } catch (err: any) {
    errorMessage.set(err?.message || "Erreur lors de l'anonymisation");
    currentJobId.set(null);
  } finally {
    isLoading.set(false);
  }
}
