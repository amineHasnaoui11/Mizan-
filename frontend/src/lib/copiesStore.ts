import type { Correction } from "./api";

/**
 * Copies corrigées ET validées par le prof (localStorage, en attendant la BD).
 * On stocke la correction finale (notes ajustées par le prof) + un peu de méta.
 */
const KEY = "mizan.copies";

export interface CopieValidee {
  copie_id: string;
  devoir_id: string;
  eleve: string;
  classe: string;
  correction: Correction;
  valide_le: string; // ISO
}

export function listCopies(): CopieValidee[] {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? "[]");
  } catch {
    return [];
  }
}

export function saveCopie(c: Omit<CopieValidee, "valide_le">): CopieValidee {
  const copies = listCopies();
  const entry: CopieValidee = { ...c, valide_le: new Date().toISOString() };
  const i = copies.findIndex((x) => x.copie_id === c.copie_id && x.devoir_id === c.devoir_id);
  if (i >= 0) copies[i] = entry;
  else copies.unshift(entry);
  localStorage.setItem(KEY, JSON.stringify(copies));
  return entry;
}
