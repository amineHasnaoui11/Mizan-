/**
 * Client API vers le backend FastAPI (via le proxy /api en dev).
 * Types alignés sur les schémas Pydantic de `mizan/schemas.py`.
 */
const BASE = import.meta.env.VITE_API_URL ?? "/api";

export interface CritereBareme {
  critere: string;
  points_max: number;
  regle: string;
}
export interface QuestionReference {
  numero: number;
  enonce: string;
  type: "factuelle" | "qcm" | "calcul" | "ouverte";
  corrige: string;
  note_max: number;
  bareme: CritereBareme[];
}
export interface Reference {
  devoir_id: string;
  matiere?: string;
  niveau?: string;
  langue?: "fr" | "ar" | "mixte";
  note_max_devoir: number;
  questions: QuestionReference[];
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
  langue_detectee: "fr" | "ar" | "mixte";
  note_globale: number;
  note_max: number;
  questions: QuestionCorrigee[];
  feedback_global: string;
}

async function jsonOrThrow<T>(resp: Response): Promise<T> {
  if (!resp.ok) throw new Error(`${resp.status} : ${await resp.text()}`);
  return resp.json() as Promise<T>;
}

/** Construit le barème à partir des documents du prof (devoir + barème + corrigé). */
export async function construireReference(docs: {
  devoir: File[];
  bareme: File[];
  corrige: File[];
  matiere?: string;
  niveau?: string;
  langue?: string;
  devoirId?: string;
}): Promise<Reference> {
  const fd = new FormData();
  docs.devoir.forEach((f) => fd.append("devoir", f));
  docs.bareme.forEach((f) => fd.append("bareme", f));
  docs.corrige.forEach((f) => fd.append("corrige", f));
  fd.append("matiere", docs.matiere ?? "");
  fd.append("niveau", docs.niveau ?? "");
  fd.append("langue", docs.langue ?? "mixte");
  fd.append("devoir_id", docs.devoirId ?? "");
  return jsonOrThrow(await fetch(`${BASE}/construire-reference`, { method: "POST", body: fd }));
}

/** Transcrit une copie (1..N pages) — étape 1 du human-in-the-loop. */
export async function transcrire(
  reference: Reference,
  copieId: string,
  fichiers: File[],
): Promise<{ transcriptions: { numero: number; transcription: string }[] }> {
  const fd = new FormData();
  fd.append("reference", JSON.stringify(reference));
  fd.append("copie_id", copieId);
  fichiers.forEach((f) => fd.append("copie", f));
  return jsonOrThrow(await fetch(`${BASE}/transcrire`, { method: "POST", body: fd }));
}

/** Note une transcription validée par le prof — étape 3. */
export async function noter(
  reference: Reference,
  copieId: string,
  transcriptions: { numero: number; transcription: string }[],
): Promise<Correction> {
  return jsonOrThrow(
    await fetch(`${BASE}/noter`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reference, copie_id: copieId, transcriptions }),
    }),
  );
}
