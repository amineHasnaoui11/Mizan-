import { API_BASE } from "./config";

// --- Types (miroir des schémas backend) ---
export interface QuestionReference {
  numero: number;
  enonce: string;
  type: string;
  corrige: string;
  note_max: number;
  bareme: { critere: string; points_max: number; regle: string }[];
}
export interface Reference {
  devoir_id: string;
  matiere?: string;
  niveau?: string;
  langue?: string;
  note_max_devoir: number;
  questions: QuestionReference[];
}
export interface DevoirResume {
  devoir_id: string;
  matiere: string;
  niveau: string;
  note_max_devoir: number;
  nb_questions: number;
}
export interface CritereEvalue {
  critere: string;
  points_obtenus: number;
  points_max: number;
  justification: string;
}
export interface QuestionCorrigee {
  numero: number;
  transcription: string;
  note: number;
  note_max: number;
  criteres: CritereEvalue[];
  feedback: string;
  confiance?: number;
  a_verifier?: boolean;
  raison_doute?: string;
}
export interface Correction {
  copie_id: string;
  langue_detectee: string;
  note_globale: number;
  note_max: number;
  questions: QuestionCorrigee[];
  feedback_global: string;
}

export interface ImagePage {
  uri: string;
  name: string;
  type: string;
}

async function jsonOrThrow<T>(resp: Response): Promise<T> {
  if (!resp.ok) throw new Error(`${resp.status} : ${await resp.text()}`);
  return (await resp.json()) as T;
}

export async function listerDevoirs(): Promise<DevoirResume[]> {
  return jsonOrThrow(await fetch(`${API_BASE}/devoirs`));
}

export async function construireReference(docs: {
  devoir: ImagePage[];
  bareme: ImagePage[];
  corrige: ImagePage[];
  matiere?: string;
  niveau?: string;
}): Promise<Reference> {
  const fd = new FormData();
  docs.devoir.forEach((p) => fd.append("devoir", p as unknown as Blob));
  docs.bareme.forEach((p) => fd.append("bareme", p as unknown as Blob));
  docs.corrige.forEach((p) => fd.append("corrige", p as unknown as Blob));
  fd.append("matiere", docs.matiere ?? "");
  fd.append("niveau", docs.niveau ?? "");
  fd.append("langue", "mixte");
  fd.append("devoir_id", "");
  return jsonOrThrow(await fetch(`${API_BASE}/construire-reference`, { method: "POST", body: fd }));
}

export async function enregistrerDevoir(reference: Reference): Promise<{ devoir_id: string }> {
  return jsonOrThrow(
    await fetch(`${API_BASE}/devoirs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(reference),
    }),
  );
}

export async function obtenirDevoir(id: string): Promise<Reference> {
  return jsonOrThrow(await fetch(`${API_BASE}/devoirs/${id}`));
}

export async function transcrire(
  reference: Reference,
  copieId: string,
  pages: ImagePage[],
): Promise<{ transcriptions: { numero: number; transcription: string }[] }> {
  const fd = new FormData();
  fd.append("reference", JSON.stringify(reference));
  fd.append("copie_id", copieId);
  // En React Native, un fichier = { uri, name, type }
  pages.forEach((p) => fd.append("copie", p as unknown as Blob));
  return jsonOrThrow(await fetch(`${API_BASE}/transcrire`, { method: "POST", body: fd }));
}

export async function enregistrerCopie(payload: {
  devoir_id: string;
  eleve: string;
  classe: string;
  correction: Correction;
}): Promise<{ jeton: string; lien: string }> {
  return jsonOrThrow(
    await fetch(`${API_BASE}/copies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  );
}

export async function assistant(pages: ImagePage[], consigne: string): Promise<{ texte: string }> {
  const fd = new FormData();
  pages.forEach((p) => fd.append("copie", p as unknown as Blob));
  fd.append("consigne", consigne);
  return jsonOrThrow(await fetch(`${API_BASE}/assistant`, { method: "POST", body: fd }));
}

export async function noter(
  reference: Reference,
  copieId: string,
  transcriptions: { numero: number; transcription: string }[],
): Promise<Correction> {
  return jsonOrThrow(
    await fetch(`${API_BASE}/noter`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reference, copie_id: copieId, transcriptions }),
    }),
  );
}
