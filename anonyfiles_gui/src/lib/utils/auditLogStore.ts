import { writable } from 'svelte/store';

export const auditLogStore = writable([]);
export const totalEntitiesStore = writable(0);
