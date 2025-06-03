// #anonyfiles/anonyfiles_gui/src/lib/stores/customReplacementRules.ts
import { writable } from 'svelte/store';

export interface CustomReplacementRule {
  pattern: string;
  replacement: string;
  isRegex?: boolean;
}

export const customReplacementRules = writable<CustomReplacementRule[]>([]);
