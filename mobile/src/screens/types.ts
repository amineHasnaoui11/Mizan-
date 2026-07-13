import type { Correction } from "../api";

export type RootStackParamList = {
  Accueil: undefined;
  Devoirs: undefined;
  NouveauDevoir: undefined;
  Scan: { devoirId?: string } | undefined;
  Resultat: { correction: Correction; eleve: string; devoirId: string; classe: string };
  Exercice: undefined;
  Analyse: { devoirId: string; matiere: string };
};
