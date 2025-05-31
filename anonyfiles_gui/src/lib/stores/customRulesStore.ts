import { writable } from 'svelte/store';

export const customReplacementRules = writable<
  { pattern: string; replacement: string; isRegex?: boolean }[]
>([]);
