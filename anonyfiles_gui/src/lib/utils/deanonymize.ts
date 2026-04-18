import { get } from 'svelte/store';
import {
  fileToDeanonymize,
  mappingFile,
  isDeanonymizing,
  deanonymizedText,
  deanonymizationError
} from '$lib/stores/deanonymizationStore';
import { apiUrl, pollJob } from './api';

export async function runDeanonymization(permissive: boolean = false) {
  const currentFileToDeanonymize = get(fileToDeanonymize);
  const currentMappingFile = get(mappingFile);

  if (!currentFileToDeanonymize || !currentMappingFile) {
    deanonymizationError.set('Veuillez sélectionner le fichier à désanonymiser ET le fichier de mapping.');
    return;
  }

  isDeanonymizing.set(true);
  deanonymizationError.set('');
  deanonymizedText.set('');

  try {
    const formData = new FormData();
    formData.append('file', currentFileToDeanonymize);
    formData.append('mapping', currentMappingFile);
    formData.append('permissive', String(permissive));

    const response = await fetch(await apiUrl('deanonymize/'), {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errMsg = await response.text();
      throw new Error(`[${response.status}] Erreur backend: ${errMsg}`);
    }

    const data = await response.json();

    if (data.job_id) {
      const pollData = await pollJob<{
        status: string;
        deanonymized_text?: string;
        error?: string;
      }>(await apiUrl(`deanonymize_status/${data.job_id}`));
      deanonymizedText.set(pollData.deanonymized_text || '');
    } else {
      deanonymizedText.set(data.deanonymized_text || '');
    }
  } catch (err: any) {
    deanonymizationError.set(err?.message || 'Erreur lors de la désanonymisation.');
  } finally {
    isDeanonymizing.set(false);
  }
}
