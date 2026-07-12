import type { Correction } from "../api";

export type RootStackParamList = {
  Accueil: undefined;
  Scan: undefined;
  Resultat: { correction: Correction; eleve: string };
  Exercice: undefined;
};
