import type { Reference } from "./api";

/**
 * Persistance locale des devoirs (localStorage) en attendant la base de
 * données (Phase 5). Chaque devoir est une Reference (barème + corrigé type).
 */
const KEY = "mizan.devoirs";

export interface DevoirStocke extends Reference {
  cree_le: string; // ISO
}

export function listDevoirs(): DevoirStocke[] {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? "[]");
  } catch {
    return [];
  }
}

export function getDevoir(id: string): DevoirStocke | undefined {
  return listDevoirs().find((d) => d.devoir_id === id);
}

export function saveDevoir(ref: Reference): DevoirStocke {
  const devoirs = listDevoirs();
  const entry: DevoirStocke = { ...ref, cree_le: new Date().toISOString() };
  const i = devoirs.findIndex((d) => d.devoir_id === ref.devoir_id);
  if (i >= 0) devoirs[i] = entry;
  else devoirs.unshift(entry);
  localStorage.setItem(KEY, JSON.stringify(devoirs));
  return entry;
}

export function deleteDevoir(id: string): void {
  localStorage.setItem(KEY, JSON.stringify(listDevoirs().filter((d) => d.devoir_id !== id)));
}
