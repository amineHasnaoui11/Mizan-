import { useState } from "react";
import { Link } from "react-router-dom";
import { FileUp, ScanLine, Wand2, CheckCircle2, Inbox } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardBody } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Textarea, Field } from "@/components/ui/Input";
import { Spinner } from "@/components/ui/Spinner";
import { UploadZone } from "@/features/devoirs/UploadZone";
import { listDevoirs } from "@/lib/devoirsStore";
import { saveCopie } from "@/lib/copiesStore";
import { transcrire, noter, type Correction } from "@/lib/api";
import { CorrectionResultat } from "./CorrectionResultat";

type Ligne = { numero: number; transcription: string };

export function CorrectionPage() {
  const devoirs = listDevoirs();
  const [devoirId, setDevoirId] = useState(devoirs[0]?.devoir_id ?? "");
  const [eleve, setEleve] = useState("");
  const [classe, setClasse] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [transcriptions, setTranscriptions] = useState<Ligne[] | null>(null);
  const [correction, setCorrection] = useState<Correction | null>(null);
  const [loading, setLoading] = useState<null | "lecture" | "notation">(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [valide, setValide] = useState(false);

  const devoir = devoirs.find((d) => d.devoir_id === devoirId);
  const copieId = eleve.trim() ? eleve.trim().replace(/\s+/g, "_").toLowerCase() : "eleve";

  if (devoirs.length === 0) {
    return (
      <>
        <PageHeader title="Correction" subtitle="Déposez une copie, l'IA pré-note" />
        <Card>
          <CardBody className="flex flex-col items-center justify-center gap-3 py-16 text-center">
            <div className="grid h-14 w-14 place-items-center rounded-2xl bg-ink/6 text-muted">
              <Inbox size={26} />
            </div>
            <p className="text-sm font-medium text-ink">Aucun devoir à corriger</p>
            <p className="text-sm text-muted">Crée d'abord un devoir (barème + corrigé type).</p>
            <Link to="/devoirs">
              <Button variant="accent" className="mt-1">Aller aux devoirs</Button>
            </Link>
          </CardBody>
        </Card>
      </>
    );
  }

  async function lireCopie() {
    if (!devoir) return;
    setLoading("lecture");
    setErreur(null);
    setCorrection(null);
    try {
      const r = await transcrire(devoir, copieId, files);
      setTranscriptions(
        r.transcriptions.length
          ? r.transcriptions
          : devoir.questions.map((q) => ({ numero: q.numero, transcription: "" })),
      );
    } catch (e) {
      setErreur(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(null);
    }
  }

  async function noterCopie() {
    if (!devoir || !transcriptions) return;
    setLoading("notation");
    setErreur(null);
    try {
      setCorrection(await noter(devoir, copieId, transcriptions));
    } catch (e) {
      setErreur(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(null);
    }
  }

  function valider() {
    if (!correction || !devoir) return;
    saveCopie({
      copie_id: copieId,
      devoir_id: devoir.devoir_id,
      eleve: eleve.trim() || copieId,
      classe: classe.trim(),
      correction,
    });
    setValide(true);
  }

  function recommencer() {
    setFiles([]);
    setTranscriptions(null);
    setCorrection(null);
    setValide(false);
    setEleve("");
  }

  if (valide) {
    return (
      <>
        <PageHeader title="Correction" subtitle="Déposez une copie, l'IA pré-note" />
        <Card>
          <CardBody className="flex flex-col items-center justify-center gap-3 py-16 text-center">
            <div className="grid h-14 w-14 place-items-center rounded-2xl bg-score-full/12 text-score-full">
              <CheckCircle2 size={28} />
            </div>
            <p className="text-sm font-medium text-ink">Note validée et enregistrée ✓</p>
            <Button variant="accent" onClick={recommencer} className="mt-1">
              Corriger une autre copie
            </Button>
          </CardBody>
        </Card>
      </>
    );
  }

  return (
    <>
      <PageHeader title="Correction" subtitle="Déposez une copie, l'IA pré-note — vous validez" />

      <Card>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <Field label="Devoir">
              <select
                value={devoirId}
                onChange={(e) => setDevoirId(e.target.value)}
                className="w-full rounded-xl border border-line bg-surface px-3 py-2.5 text-sm text-ink"
              >
                {devoirs.map((d) => (
                  <option key={d.devoir_id} value={d.devoir_id}>
                    {d.matiere || d.devoir_id} · {d.note_max_devoir} pts
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Élève">
              <Input value={eleve} onChange={(e) => setEleve(e.target.value)} placeholder="Ex : Aziz Abdelli" />
            </Field>
            <Field label="Classe">
              <Input value={classe} onChange={(e) => setClasse(e.target.value)} placeholder="Ex : 6ème B" />
            </Field>
          </div>

          <UploadZone
            label="Copie de l'élève"
            hint="images ou PDF, plusieurs pages"
            icon={FileUp}
            files={files}
            onChange={setFiles}
          />

          {erreur && (
            <div className="rounded-xl bg-score-zero/10 px-3 py-2 text-sm text-score-zero">{erreur}</div>
          )}

          <Button variant="accent" onClick={lireCopie} disabled={files.length === 0 || loading !== null}>
            {loading === "lecture" ? <Spinner /> : <ScanLine size={18} />}
            {loading === "lecture" ? "Lecture de la copie…" : "① Lire la copie"}
          </Button>
        </CardBody>
      </Card>

      {transcriptions && !correction && (
        <Card className="mt-4">
          <CardBody className="space-y-3">
            <div>
              <h2 className="text-lg font-semibold text-ink">② Relis ce que l'IA a lu</h2>
              <p className="text-sm text-muted">Corrige la transcription si besoin avant de noter.</p>
            </div>
            {transcriptions.map((t) => (
              <Field key={t.numero} label={`Question ${t.numero}`}>
                <Textarea
                  value={t.transcription}
                  rows={2}
                  onChange={(e) =>
                    setTranscriptions((prev) =>
                      (prev ?? []).map((x) => (x.numero === t.numero ? { ...x, transcription: e.target.value } : x)),
                    )
                  }
                />
              </Field>
            ))}
            <Button variant="accent" onClick={noterCopie} disabled={loading !== null}>
              {loading === "notation" ? <Spinner /> : <Wand2 size={18} />}
              {loading === "notation" ? "Notation en cours…" : "③ Noter la copie"}
            </Button>
          </CardBody>
        </Card>
      )}

      {correction && (
        <div className="mt-4">
          <CorrectionResultat correction={correction} onChange={setCorrection} onValider={valider} />
        </div>
      )}
    </>
  );
}
