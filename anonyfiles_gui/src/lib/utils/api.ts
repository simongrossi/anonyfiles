import { isTauri } from './runtime';

let apiBasePromise: Promise<string> | null = null;

async function resolveApiBase(): Promise<string> {
  if (isTauri()) {
    const { invoke } = await import('@tauri-apps/api/core');
    const port = await invoke<number>('get_api_port');
    return `http://127.0.0.1:${port}`;
  }
  const raw = import.meta.env.VITE_ANONYFILES_API_URL ?? 'http://127.0.0.1:8000';
  return String(raw).replace(/\/+$/, '').replace(/\/api$/, '');
}

export function getApiBase(): Promise<string> {
  return apiBasePromise ??= resolveApiBase();
}

export async function apiUrl(path: string): Promise<string> {
  const base = await getApiBase();
  return `${base}/api/${path.replace(/^\/+/, '')}`;
}

export async function waitForApiReady(timeoutMs = 60_000): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  const url = await apiUrl('health');
  let lastError: unknown = null;
  while (Date.now() < deadline) {
    try {
      const resp = await fetch(url);
      if (resp.ok) return;
    } catch (err) {
      lastError = err;
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error(`API not ready after ${timeoutMs}ms: ${String(lastError ?? 'no response')}`);
}

export function debug(...args: unknown[]): void {
  if (import.meta.env.DEV) console.log(...args);
}

export function debugError(...args: unknown[]): void {
  if (import.meta.env.DEV) console.error(...args);
}

export interface PollJobOptions {
  maxMs?: number;
  baseMs?: number;
  capMs?: number;
  signal?: AbortSignal;
}

export type JobStatus = 'pending' | 'running' | 'finished' | 'error' | string;

export interface JobStatusPayload {
  status: JobStatus;
  error?: string;
  [key: string]: unknown;
}

export class PollTimeoutError extends Error {
  constructor(message = 'Polling timeout') {
    super(message);
    this.name = 'PollTimeoutError';
  }
}

export async function pollJob<T extends JobStatusPayload = JobStatusPayload>(
  statusUrl: string,
  { maxMs = 300_000, baseMs = 1000, capMs = 5000, signal }: PollJobOptions = {}
): Promise<T> {
  const deadline = Date.now() + maxMs;
  let attempt = 0;

  while (true) {
    if (signal?.aborted) throw new DOMException('Aborted', 'AbortError');
    if (Date.now() > deadline) throw new PollTimeoutError();

    const delay = Math.min(baseMs * Math.pow(1.5, attempt), capMs);
    await new Promise<void>((resolve, reject) => {
      const t = setTimeout(() => resolve(), delay);
      if (signal) {
        signal.addEventListener('abort', () => {
          clearTimeout(t);
          reject(new DOMException('Aborted', 'AbortError'));
        }, { once: true });
      }
    });
    attempt++;

    const resp = await fetch(statusUrl, { signal });

    if (resp.status === 429) {
      const retryAfter = Number(resp.headers.get('Retry-After'));
      if (Number.isFinite(retryAfter) && retryAfter > 0) {
        await new Promise((r) => setTimeout(r, retryAfter * 1000));
      }
      continue;
    }

    if (!resp.ok) {
      const text = await resp.text().catch(() => '');
      let detail = `HTTP ${resp.status}`;
      try {
        const parsed = JSON.parse(text);
        detail = parsed.detail ?? detail;
      } catch {
        if (text) detail = text;
      }
      throw new Error(detail);
    }

    const data = (await resp.json()) as T;

    if (data.status === 'finished') return data;
    if (data.status === 'error') throw new Error(data.error || 'Erreur inconnue lors du polling');
  }
}
