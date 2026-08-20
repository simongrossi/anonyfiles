import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

vi.mock('./api', () => ({ debugError: vi.fn() }));

const isTauriMock = vi.fn(() => false);
vi.mock('./runtime', () => ({ isTauri: () => isTauriMock() }));

const saveMock = vi.fn();
const writeFileMock = vi.fn();
vi.mock('@tauri-apps/plugin-dialog', () => ({ save: (...args: unknown[]) => saveMock(...args) }));
vi.mock('@tauri-apps/plugin-fs', () => ({
  writeFile: (...args: unknown[]) => writeFileMock(...args),
}));

import { saveFile, saveTextFile, suffixedFileName } from './download';

describe('suffixedFileName', () => {
  it('insère le suffixe avant l’extension', () => {
    expect(suffixedFileName('contrat.docx', '_anonymise', 'out.txt')).toBe(
      'contrat_anonymise.docx'
    );
  });

  it('gère un nom sans extension', () => {
    expect(suffixedFileName('contrat', '_anonymise', 'out.txt')).toBe('contrat_anonymise');
  });

  it('préserve les points internes', () => {
    expect(suffixedFileName('rapport.v2.pdf', '_anonymise', 'out.txt')).toBe(
      'rapport.v2_anonymise.pdf'
    );
  });

  it('retombe sur le nom par défaut si le nom d’origine est vide', () => {
    expect(suffixedFileName('', '_anonymise', 'anonymized.txt')).toBe('anonymized.txt');
  });
});

describe('saveFile', () => {
  beforeEach(() => {
    saveMock.mockReset();
    writeFileMock.mockReset();
    isTauriMock.mockReturnValue(false);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('utilise un <a download> hors Tauri', async () => {
    // L'environnement Vitest est `node` : on stubbe le strict minimum du DOM.
    const anchor = { download: '', href: '', click: vi.fn(), remove: vi.fn() };
    vi.stubGlobal('document', {
      createElement: vi.fn(() => anchor),
      body: { appendChild: vi.fn() },
    });
    vi.stubGlobal('URL', {
      createObjectURL: vi.fn(() => 'blob:x'),
      revokeObjectURL: vi.fn(),
    });

    expect(await saveTextFile('coucou', 'a.txt')).toBe('saved');
    expect(anchor.click).toHaveBeenCalled();
    expect(anchor.download).toBe('a.txt');
    expect(saveMock).not.toHaveBeenCalled();

    vi.unstubAllGlobals();
  });

  it('passe par la boîte de dialogue native dans Tauri', async () => {
    // C'est le cœur de l'issue #76 : dans WKWebView (macOS), <a download> est
    // ignoré silencieusement, seul le plugin fs écrit réellement le fichier.
    isTauriMock.mockReturnValue(true);
    saveMock.mockResolvedValue('/Users/greg/Desktop/contrat_anonymise.docx');
    writeFileMock.mockResolvedValue(undefined);

    const bytes = new Uint8Array([1, 2, 3]).buffer;
    expect(await saveFile(bytes, 'contrat_anonymise.docx')).toBe('saved');

    expect(saveMock).toHaveBeenCalledWith({
      defaultPath: 'contrat_anonymise.docx',
      filters: [{ name: 'DOCX', extensions: ['docx'] }],
    });
    const [path, written] = writeFileMock.mock.calls[0];
    expect(path).toBe('/Users/greg/Desktop/contrat_anonymise.docx');
    expect(Array.from(written as Uint8Array)).toEqual([1, 2, 3]);
  });

  it('renvoie "cancelled" quand la boîte de dialogue est fermée', async () => {
    isTauriMock.mockReturnValue(true);
    saveMock.mockResolvedValue(null);

    expect(await saveTextFile('coucou', 'a.txt')).toBe('cancelled');
    expect(writeFileMock).not.toHaveBeenCalled();
  });

  it('renvoie "error" si l’écriture échoue', async () => {
    isTauriMock.mockReturnValue(true);
    saveMock.mockResolvedValue('/tmp/a.txt');
    writeFileMock.mockRejectedValue(new Error('forbidden path'));

    expect(await saveTextFile('coucou', 'a.txt')).toBe('error');
  });
});
