import { describe, it, expect, beforeEach, vi } from 'vitest';

// On mocke la couche réseau/polling pour n'observer QUE la construction de la
// requête (FormData) envoyée au backend. C'est exactement ce qui était cassé
// dans l'issue #73 : le champ `file` n'était jamais ajouté pour docx/pdf/json.
vi.mock('./api', () => ({
  apiUrl: vi.fn(async (p: string) => `http://test/api/${p}`),
  pollJob: vi.fn(async () => ({
    status: 'finished',
    anonymized_text: 'ok',
    audit_log: [],
    mapping_csv: '',
  })),
  debug: vi.fn(),
  debugError: vi.fn(),
}));

import { runAnonymization } from './anonymize';
import { inputText, errorMessage } from '../stores/anonymizationStore';
import { get } from 'svelte/store';

let lastBody: FormData | null = null;
let fetchCalls = 0;

beforeEach(() => {
  lastBody = null;
  fetchCalls = 0;
  inputText.set('Bonjour Jean Dupont');
  errorMessage.set('');
  globalThis.fetch = vi.fn(async (_url: unknown, init: any) => {
    fetchCalls += 1;
    lastBody = init.body as FormData;
    return {
      ok: true,
      json: async () => ({ job_id: 'job-123' }),
      text: async () => '',
    };
  }) as unknown as typeof fetch;
});

function makeFile(name: string): File {
  return new File([new Uint8Array([0x50, 0x4b, 0x03, 0x04])], name);
}

describe('runAnonymization — construction du FormData par type de fichier', () => {
  it('txt : envoie le contenu texte comme fichier', async () => {
    await runAnonymization({ fileType: 'txt', fileName: 'note.txt', selected: {} });
    expect(fetchCalls).toBe(1);
    expect(lastBody!.has('file')).toBe(true);
    expect((lastBody!.get('file') as File).name).toBe('note.txt');
    expect(lastBody!.get('file_type')).toBe('txt');
    expect(lastBody!.has('has_header')).toBe(false);
  });

  it('json : envoie le contenu comme fichier .json', async () => {
    await runAnonymization({ fileType: 'json', fileName: 'data.json', selected: {} });
    expect(lastBody!.has('file')).toBe(true);
    expect((lastBody!.get('file') as File).name).toBe('data.json');
    expect(lastBody!.get('file_type')).toBe('json');
  });

  it('docx : joint bien le fichier binaire (régression issue #73)', async () => {
    const file = makeFile('rapport.docx');
    await runAnonymization({ fileType: 'docx', fileName: 'rapport.docx', xlsxFile: file, selected: {} });
    expect(fetchCalls).toBe(1);
    expect(lastBody!.has('file')).toBe(true);
    expect((lastBody!.get('file') as File).name).toBe('rapport.docx');
    expect(lastBody!.get('file_type')).toBe('docx');
    // docx n'est pas tabulaire : pas de has_header
    expect(lastBody!.has('has_header')).toBe(false);
  });

  it('pdf : joint bien le fichier binaire', async () => {
    const file = makeFile('contrat.pdf');
    await runAnonymization({ fileType: 'pdf', fileName: 'contrat.pdf', xlsxFile: file, selected: {} });
    expect(lastBody!.has('file')).toBe(true);
    expect((lastBody!.get('file') as File).name).toBe('contrat.pdf');
    expect(lastBody!.get('file_type')).toBe('pdf');
  });

  it('csv : joint le fichier et ajoute has_header', async () => {
    const file = makeFile('clients.csv');
    await runAnonymization({ fileType: 'csv', fileName: 'clients.csv', xlsxFile: file, hasHeader: true, selected: {} });
    expect(lastBody!.has('file')).toBe(true);
    expect(lastBody!.get('has_header')).toBe('true');
  });

  it('xlsx : joint le fichier et ajoute has_header', async () => {
    const file = makeFile('table.xlsx');
    await runAnonymization({ fileType: 'xlsx', fileName: 'table.xlsx', xlsxFile: file, hasHeader: false, selected: {} });
    expect(lastBody!.has('file')).toBe(true);
    expect(lastBody!.get('has_header')).toBe('false');
  });

  it('docx sans fichier : ne fait pas d’appel et remonte une erreur claire', async () => {
    await runAnonymization({ fileType: 'docx', fileName: 'rapport.docx', xlsxFile: null, selected: {} });
    expect(fetchCalls).toBe(0);
    expect(get(errorMessage)).toContain('Fichier manquant');
  });
});
