import { useState } from "react";
import { FileText, ClipboardList, PenLine, Wand2, Save, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { Input, Field } from "@/components/ui/Input";
import { Spinner } from "@/components/ui/Spinner";
import { construireReference, type Reference, type QuestionReference } from "@/lib/api";
import { saveDevoir } from "@/lib/devoirsStore";
import { UploadZone } from "./UploadZone";
import { QuestionEditor } from "./QuestionEditor";

export function NouveauDevoir({ onDone, onCancel }: { onDone: () => void; onCancel: () => void }) {
  const [matiere, setMatiere] = useState("");
  const [niveau, setNiveau] = useState("");
  const [devoir, setDevoir] = useState<File[]>([]);
  const [bareme, setBareme] = useState<File[]>([]);
  const [corrige, setCorrige] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const [ref, setRef] = useState<Reference | null>(null);

  const peutConstruire = devoir.length + bareme.length + corrige.length > 0;

  async function construire() {
    setLoading(true);
    setErreur(null);
    try {
      const r = await construireReference({ devoir, bareme, corrige, matiere, niveau });
      setRef(r);
    } catch (e) {
      setErreur(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  function majQuestion(next: QuestionReference) {
    if (!ref) return;
    setRef({ ...ref, questions: ref.questions.map((q) => (q.numero === next.numero ? next : q)) });
  }

  function enregistrer() {
    if (!ref) return;
    const total = ref.questions.reduce((s, q) => s + (q.note_max || 0), 0);
    saveDevoir({ ...ref, note_max_devoir: Math.round(total * 100) / 100 });
    onDone();
  }

  const total = ref?.questions.reduce((s, q) => s + (q.note_max || 0), 0) ?? 0;

  return (
    <>
      <button
        onClick={onCancel}
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted hover:text-ink"
      >
        <ArrowLeft size={16} /> Retour
      </button>

      {!ref ? (
        <>
          <Card>
            <CardBody className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <Field label="Matière">
                  <Input value={matiere} onChange={(e) => setMatiere(e.target.value)} placeholder="Ex : الإيقاظ العلمي" />
                </Field>
                <Field label="Niveau / classe">
                  <Input value={niveau} onChange={(e) => setNiveau(e.target.value)} placeholder="Ex : 6ème" />
                </Field>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <UploadZone
                  label="Devoir vierge"
                  hint="les énoncés"
                  icon={FileText}
                  files={devoir}
                  onChange={setDevoir}
                />
                <UploadZone
                  label="Barème"
                  hint="les points"
                  icon={ClipboardList}
                  files={bareme}
                  onChange={setBareme}
                />
                <UploadZone
                  label="Ta correction"
                  hint="les réponses attendues"
                  icon={PenLine}
                  files={corrige}
                  onChange={setCorrige}
                />
              </div>

              <p className="text-xs text-muted">
                Images ou PDF, plusieurs pages possibles. Mizan lit les documents et construit le
                barème ; tu pourras le relire et le corriger avant d'enregistrer.
              </p>

              {erreur && (
                <div className="rounded-xl bg-score-zero/10 px-3 py-2 text-sm text-score-zero">{erreur}</div>
              )}

              <Button variant="accent" onClick={construire} disabled={!peutConstruire || loading}>
                {loading ? <Spinner /> : <Wand2 size={18} />}
                {loading ? "Construction du barème…" : "Construire le barème"}
              </Button>
            </CardBody>
          </Card>
        </>
      ) : (
        <>
          <div className="mb-4 flex items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-ink">{ref.matiere || "Devoir"}</h2>
              <p className="text-sm text-muted">
                {ref.questions.length} questions · total{" "}
                <span className="font-mono font-semibold text-ink">{Math.round(total * 100) / 100}</span> pts
              </p>
            </div>
            <Button variant="accent" onClick={enregistrer}>
              <Save size={18} /> Enregistrer le devoir
            </Button>
          </div>
          <p className="mb-3 text-sm text-muted">
            Relis le barème proposé et corrige-le si besoin (énoncé, points, corrigé type).
          </p>
          <div className="space-y-3">
            {ref.questions.map((q) => (
              <QuestionEditor key={q.numero} q={q} onChange={majQuestion} />
            ))}
          </div>
        </>
      )}
    </>
  );
}
