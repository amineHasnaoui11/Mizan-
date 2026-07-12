import { AlertTriangle, Save, CheckCircle2 } from "lucide-react";
import type { Correction, QuestionCorrigee } from "@/lib/api";
import { Card, CardBody } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { couleurNote } from "@/lib/utils";

/**
 * Résultat de correction : note globale + détail par question. Le prof PEUT
 * ajuster les points de chaque question puis valider (sa décision prime).
 */
export function CorrectionResultat({
  correction,
  onChange,
  onValider,
}: {
  correction: Correction;
  onChange: (c: Correction) => void;
  onValider: () => void;
}) {
  const total = correction.questions.reduce((s, q) => s + (q.note || 0), 0);
  const totalMax = correction.questions.reduce((s, q) => s + (q.note_max || 0), 0);
  const aVerifier = correction.questions.filter((q) => q.a_verifier);

  function setNote(numero: number, note: number) {
    onChange({
      ...correction,
      questions: correction.questions.map((q) =>
        q.numero === numero ? { ...q, note, a_verifier: false } : q,
      ),
    });
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardBody className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-sm text-muted">Note proposée (ajustable)</div>
            <div className="font-mono text-3xl font-semibold" style={{ color: couleurNote(total, totalMax) }}>
              {Math.round(total * 100) / 100} <span className="text-lg text-muted">/ {Math.round(totalMax * 100) / 100}</span>
            </div>
          </div>
          <Button variant="accent" onClick={onValider}>
            <Save size={18} /> Valider la note
          </Button>
        </CardBody>
      </Card>

      {correction.feedback_global && (
        <div className="rounded-xl bg-ink/5 px-4 py-3 text-sm text-ink">{correction.feedback_global}</div>
      )}

      {aVerifier.length > 0 && (
        <div className="flex items-start gap-2 rounded-xl bg-score-partial/12 px-4 py-3 text-sm text-ink">
          <AlertTriangle size={18} className="mt-0.5 shrink-0 text-score-partial" />
          <span>
            <strong>{aVerifier.length} question(s) à vérifier</strong> (
            {aVerifier.map((q) => `Q${q.numero}`).join(", ")}) — l'IA a un doute, ta décision prime.
          </span>
        </div>
      )}

      <div className="space-y-3">
        {correction.questions.map((q) => (
          <QuestionResultat key={q.numero} q={q} onNote={(n) => setNote(q.numero, n)} />
        ))}
      </div>
    </div>
  );
}

function QuestionResultat({ q, onNote }: { q: QuestionCorrigee; onNote: (n: number) => void }) {
  const couleur = couleurNote(q.note, q.note_max);
  return (
    <Card className={q.a_verifier ? "ring-2 ring-score-partial/40" : ""}>
      <CardBody className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-ink">Question {q.numero}</span>
            {q.a_verifier && (
              <Badge color="#E8A13A">
                <AlertTriangle size={12} className="me-1 inline" /> à vérifier
              </Badge>
            )}
            {!q.a_verifier && typeof q.confiance === "number" && q.confiance >= 0.8 && (
              <Badge color="#2E7D32">
                <CheckCircle2 size={12} className="me-1 inline" /> confiance {Math.round(q.confiance * 100)}%
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-1.5">
            <Input
              type="number"
              step="0.25"
              min={0}
              max={q.note_max}
              value={q.note}
              onChange={(e) => onNote(Number(e.target.value))}
              className="w-20 text-center font-mono"
              style={{ color: couleur }}
              aria-label={`Note Q${q.numero}`}
            />
            <span className="text-sm text-muted">/ {q.note_max}</span>
          </div>
        </div>

        <div className="rounded-lg bg-ink/4 px-3 py-2 text-sm text-ink">
          <span className="text-xs text-muted">Ce que l'IA a lu : </span>
          {q.transcription || "—"}
        </div>

        {q.a_verifier && q.raison_doute && (
          <div className="text-sm text-score-partial">🤔 {q.raison_doute}</div>
        )}

        {q.criteres.map((c, i) => (
          <div key={i} className="flex items-start gap-2 text-sm">
            <Badge color={couleurNote(c.points_obtenus, c.points_max)}>
              {c.points_obtenus}/{c.points_max}
            </Badge>
            <div>
              <span className="font-medium text-ink">{c.critere}</span>
              {c.justification && <div className="text-xs text-muted">{c.justification}</div>}
            </div>
          </div>
        ))}

        {q.feedback && <div className="text-sm italic text-muted">💬 {q.feedback}</div>}
      </CardBody>
    </Card>
  );
}
