export const ANONYMIZATION_OPTION_KEYS = [
  'anonymizePersons',
  'anonymizeLocations',
  'anonymizeOrgs',
  'anonymizeEmails',
  'anonymizeDates',
  'anonymizeMisc',
  'anonymizePhones',
  'anonymizeIbans',
  'anonymizeAddresses',
] as const;

export type AnonymizationOptionKey = (typeof ANONYMIZATION_OPTION_KEYS)[number];

export type AnonymizationSelection = Record<AnonymizationOptionKey, boolean>;

export interface AnonymizationOption {
  key: AnonymizationOptionKey;
  label: string;
  default: boolean;
}

export interface AnonymizationProfile {
  id: string;
  label: string;
  description: string;
  selection: AnonymizationSelection;
}

export const ANONYMIZATION_OPTIONS: AnonymizationOption[] = [
  { key: 'anonymizePersons', label: 'Personnes (PER)', default: false },
  { key: 'anonymizeLocations', label: 'Lieux (LOC)', default: false },
  { key: 'anonymizeOrgs', label: 'Organisations (ORG)', default: false },
  { key: 'anonymizeEmails', label: 'Emails', default: false },
  { key: 'anonymizeDates', label: 'Dates', default: false },
  { key: 'anonymizeMisc', label: 'MISC', default: false },
  { key: 'anonymizePhones', label: 'Téléphones (PHONE)', default: false },
  { key: 'anonymizeIbans', label: 'IBAN', default: false },
  { key: 'anonymizeAddresses', label: 'Adresses (ADDRESS)', default: false },
];

export function createDefaultAnonymizationSelection(): AnonymizationSelection {
  return Object.fromEntries(
    ANONYMIZATION_OPTIONS.map((option) => [option.key, option.default])
  ) as AnonymizationSelection;
}

function selection(overrides: Partial<AnonymizationSelection>): AnonymizationSelection {
  return { ...createDefaultAnonymizationSelection(), ...overrides };
}

export const ANONYMIZATION_PROFILES: AnonymizationProfile[] = [
  {
    id: 'strict-rgpd',
    label: 'Strict RGPD',
    description: 'Toutes les catégories disponibles sont anonymisées.',
    selection: selection({
      anonymizePersons: true,
      anonymizeLocations: true,
      anonymizeOrgs: true,
      anonymizeEmails: true,
      anonymizeDates: true,
      anonymizeMisc: true,
      anonymizePhones: true,
      anonymizeIbans: true,
      anonymizeAddresses: true,
    }),
  },
  {
    id: 'leger',
    label: 'Léger',
    description: 'Identifiants directs uniquement.',
    selection: selection({
      anonymizePersons: true,
      anonymizeEmails: true,
      anonymizePhones: true,
      anonymizeIbans: true,
    }),
  },
  {
    id: 'documents-rh',
    label: 'Documents RH',
    description: 'Données personnelles fréquentes dans les dossiers RH.',
    selection: selection({
      anonymizePersons: true,
      anonymizeLocations: true,
      anonymizeEmails: true,
      anonymizeDates: true,
      anonymizeMisc: true,
      anonymizePhones: true,
      anonymizeIbans: true,
      anonymizeAddresses: true,
    }),
  },
  {
    id: 'contrats',
    label: 'Contrats',
    description: 'Parties, coordonnées, lieux, dates et références bancaires.',
    selection: selection({
      anonymizePersons: true,
      anonymizeLocations: true,
      anonymizeOrgs: true,
      anonymizeEmails: true,
      anonymizeDates: true,
      anonymizePhones: true,
      anonymizeIbans: true,
      anonymizeAddresses: true,
    }),
  },
  {
    id: 'logs-techniques',
    label: 'Logs techniques',
    description: 'Identifiants humains et valeurs diverses sans toucher aux dates.',
    selection: selection({
      anonymizePersons: true,
      anonymizeEmails: true,
      anonymizeMisc: true,
      anonymizePhones: true,
      anonymizeIbans: true,
    }),
  },
];

export function selectionFromProfile(
  profile: AnonymizationProfile
): AnonymizationSelection {
  return { ...profile.selection };
}

export function findMatchingAnonymizationProfile(
  selected: Partial<Record<AnonymizationOptionKey, boolean>>
): AnonymizationProfile | null {
  return (
    ANONYMIZATION_PROFILES.find((profile) =>
      ANONYMIZATION_OPTION_KEYS.every(
        (key) => Boolean(selected[key]) === profile.selection[key]
      )
    ) ?? null
  );
}
