// #anonyfiles/anonyfiles_gui/src/lib/utils/useFileHandler.ts
import { writable } from 'svelte/store';
import { inputText, outputText, errorMessage } from '../stores/anonymizationStore';

export const fileType = writable("txt");
export const fileName = writable("");
export const hasHeader = writable(true);
export const xlsxFile = writable<File | null>(null);
export const previewTable = writable<string[][]>([]);
export const previewHeaders = writable<string[]>([]);
const PREVIEW_ROW_LIMIT = 10;

function parseCsvPreview(csvText: string) {
  const rows = csvText.trim().split(/\r?\n/);
  if (!rows.length) {
    previewHeaders.set([]);
    previewTable.set([]);
    return;
  }
  let delimiter = ",";
  if (rows[0].split(";").length > rows[0].split(",").length) delimiter = ";";
  previewHeaders.set(rows[0].split(delimiter));
  previewTable.set(rows.slice(1, 1 + PREVIEW_ROW_LIMIT).map(row => row.split(delimiter)));
}

export function handleFile(file: File) {
  if (!file) return;
  inputText.set('');
  outputText.set('');
  errorMessage.set('');
  previewTable.set([]);
  previewHeaders.set([]);
  xlsxFile.set(null);

  fileName.set(file.name);
  const ext = file.name.split('.').pop()?.toLowerCase() || "";
  fileType.set(ext);

  if (["txt", "csv", "json"].includes(ext)) {
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      inputText.set(content);
      if (ext === "csv") {
        parseCsvPreview(content);
        xlsxFile.set(file); // Correction appliquée ici
      }
    };
    reader.readAsText(file, "UTF-8");
  } else if (["xlsx", "docx", "pdf"].includes(ext)) {
    if (ext === "xlsx") {
      xlsxFile.set(file);
    }
    // Note: Si vous avez besoin de traiter docx ou pdf en tant qu'objet File
    // pour l'envoyer au backend de la même manière que xlsx,
    // vous devrez également ajouter xlsxFile.set(file); pour ces extensions ici.
    // Actuellement, seul xlsx définit xlsxFile dans ce bloc.
  } else {
    errorMessage.set(`Format de fichier non pris en charge : ${ext}. Seuls les fichiers .txt, .csv, .xlsx, .docx, .pdf, .json sont acceptés.`);
    fileName.set("");
    fileType.set("txt"); // Réinitialise à un type par défaut ou gère l'erreur autrement
  }
}