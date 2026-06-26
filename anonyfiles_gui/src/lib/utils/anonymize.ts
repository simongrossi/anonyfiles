// #anonyfiles/anonyfiles_gui/src/lib/utils/anonymize.ts
import { get } from 'svelte/store';
import {
  inputText,
  outputText,
  auditLog,
  mappingCSV,
  privacyWarnings,
  isLoading,
  errorMessage,
  outputLineCount,
  outputCharCount,
  type AuditLogEntry,
  type PrivacyWarning
} from '../stores/anonymizationStore';
import { currentJobId } from '$lib/stores/jobStore';
import { apiFetch, apiUrl, pollJob, debug, debugError } from './api';

interface RunAnonymizationParams {
  fileType?: string;
  fileName?: string;
  hasHeader?: boolean;
  xlsxFile?: File | null;
  selected: Record<string, boolean>;
  customReplacementRules?: { pattern: string; replacement: string; isRegex?: boolean }[];
  entityDecisions?: EntityDecision[];
}

export interface EntityDecision {
  text: string;
  label: string;
  enabled: boolean;
  source?: 'detected' | 'manual';
}

export interface PreviewEntity extends EntityDecision {
  count: number;
}

function buildAnonymizationFormData({
  fileType,
  fileName,
  hasHeader,
  xlsxFile,
  selected,
  customReplacementRules,
  entityDecisions,
}: RunAnonymizationParams): FormData {
  const formData = new FormData();

  if (fileType === 'txt' || fileType === 'json' || !fileType) {
    // Formats textuels : le contenu est édité en mémoire (inputText) et
    // renvoyé sous forme de Blob. On conserve l'extension d'origine pour que
    // le backend sélectionne le bon processeur (.txt / .json).
    const mime = fileType === 'json' ? 'application/json' : 'text/plain';
    const defaultName = fileType === 'json' ? 'input.json' : 'input.txt';
    formData.append('file', new Blob([get(inputText)], { type: mime }), fileName || defaultName);
  } else if (['csv', 'xlsx', 'docx', 'pdf'].includes(fileType)) {
    // Formats binaires : on envoie le fichier tel quel.
    if (!xlsxFile) throw new Error(`Fichier manquant pour le type ${fileType}`);
    formData.append('file', xlsxFile, fileName);
    if (fileType === 'csv' || fileType === 'xlsx') {
      formData.append('has_header', String(!!hasHeader));
    }
  } else {
    throw new Error(`Type de fichier non pris en charge : ${fileType}`);
  }

  formData.append('config_options', JSON.stringify(selected));

  if (customReplacementRules && customReplacementRules.length > 0) {
    debug('runAnonymization - règles personnalisées envoyées :', customReplacementRules);
    formData.append('custom_replacement_rules', JSON.stringify(customReplacementRules));
  }

  if (entityDecisions && entityDecisions.length > 0) {
    formData.append('entity_decisions', JSON.stringify(entityDecisions));
  }

  formData.append('file_type', fileType || '');
  return formData;
}

export async function runAnonymization({
  fileType,
  fileName,
  hasHeader,
  xlsxFile,
  selected,
  customReplacementRules,
  entityDecisions
}: RunAnonymizationParams) {
  isLoading.set(true);
  errorMessage.set('');
  outputText.set('');
  outputLineCount.set(0);
  outputCharCount.set(0);
  auditLog.set([]);
  mappingCSV.set('');
  privacyWarnings.set([]);
  currentJobId.set(null);

  try {
    const formData = buildAnonymizationFormData({
      fileType,
      fileName,
      hasHeader,
      xlsxFile,
      selected,
      customReplacementRules,
      entityDecisions,
    });

    const response = await apiFetch(await apiUrl('anonymize/'), {
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
        privacy_warnings?: PrivacyWarning[];
        error?: string;
      }>(await apiUrl(`anonymize_status/${data.job_id}`));

      const currentOutputText = pollData.anonymized_text || '';
      outputText.set(currentOutputText);
      outputCharCount.set(currentOutputText.length);
      outputLineCount.set(currentOutputText.split('\n').length);
      auditLog.set(pollData.audit_log || []);
      mappingCSV.set(pollData.mapping_csv || '');
      privacyWarnings.set(pollData.privacy_warnings || []);
    } else {
      const directOutputText = data.outputText || data.anonymized_text || '';
      outputText.set(directOutputText);
      outputCharCount.set(directOutputText.length);
      outputLineCount.set(directOutputText.split('\n').length);
      auditLog.set(data.auditLog || data.audit_log || []);
      mappingCSV.set(data.mappingCSV || data.mapping_csv || '');
      privacyWarnings.set(data.privacyWarnings || data.privacy_warnings || []);
      currentJobId.set(null);
    }
  } catch (err: any) {
    errorMessage.set(err?.message || "Erreur lors de l'anonymisation");
    currentJobId.set(null);
  } finally {
    isLoading.set(false);
  }
}

export async function runAnonymizationPreview(
  params: RunAnonymizationParams
): Promise<PreviewEntity[]> {
  const formData = buildAnonymizationFormData(params);
  formData.delete('entity_decisions');

  const response = await apiFetch(await apiUrl('anonymize_preview/'), {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errMsg = await response.text();
    try {
      const errJson = JSON.parse(errMsg);
      throw new Error(`[${response.status}] Erreur backend: ${errJson.detail || errMsg}`);
    } catch {
      throw new Error(`[${response.status}] Erreur backend: ${errMsg}`);
    }
  }

  const data = await response.json();
  return Array.isArray(data.entities) ? data.entities : [];
}
