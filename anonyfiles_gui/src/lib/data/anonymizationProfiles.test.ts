import { describe, expect, it } from 'vitest';

import {
  ANONYMIZATION_OPTION_KEYS,
  ANONYMIZATION_PROFILES,
  createDefaultAnonymizationSelection,
  findMatchingAnonymizationProfile,
  selectionFromProfile,
} from './anonymizationProfiles';

describe('anonymizationProfiles', () => {
  it('expose les cinq profils produit prévus', () => {
    expect(ANONYMIZATION_PROFILES.map((profile) => profile.id)).toEqual([
      'strict-rgpd',
      'leger',
      'documents-rh',
      'contrats',
      'logs-techniques',
    ]);
  });

  it('conserve le défaut historique sans entité activée', () => {
    const defaults = createDefaultAnonymizationSelection();

    expect(ANONYMIZATION_OPTION_KEYS.every((key) => defaults[key] === false)).toBe(true);
  });

  it('active toutes les entités pour le profil strict RGPD', () => {
    const strict = ANONYMIZATION_PROFILES.find((profile) => profile.id === 'strict-rgpd');

    expect(strict).toBeDefined();
    expect(ANONYMIZATION_OPTION_KEYS.every((key) => strict!.selection[key] === true)).toBe(true);
  });

  it('garde une signature de sélection distincte pour chaque profil', () => {
    const signatures = ANONYMIZATION_PROFILES.map((profile) =>
      ANONYMIZATION_OPTION_KEYS.map((key) => Number(profile.selection[key])).join('')
    );

    expect(new Set(signatures).size).toBe(ANONYMIZATION_PROFILES.length);
  });

  it('détecte un profil depuis une sélection identique', () => {
    const profile = ANONYMIZATION_PROFILES.find((candidate) => candidate.id === 'contrats')!;

    expect(findMatchingAnonymizationProfile(selectionFromProfile(profile))?.id).toBe('contrats');
  });

  it('retombe en personnalisé si la sélection est modifiée', () => {
    const profile = ANONYMIZATION_PROFILES.find((candidate) => candidate.id === 'leger')!;
    const custom = {
      ...selectionFromProfile(profile),
      anonymizeDates: true,
    };

    expect(findMatchingAnonymizationProfile(custom)).toBeNull();
  });
});
