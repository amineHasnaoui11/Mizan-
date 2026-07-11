import type { QuestionReference } from "@/lib/api";
import { Card, CardBody } from "@/components/ui/Card";
import { Input, Textarea } from "@/components/ui/Input";

/** Édition d'une question du barème (énoncé, points, corrigé type). */
export function QuestionEditor({
  q,
  onChange,
}: {
  q: QuestionReference;
  onChange: (q: QuestionReference) => void;
}) {
  return (
    <Card>
      <CardBody className="space-y-3">
        <div className="flex items-center gap-3">
          <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-ink text-paper text-xs font-semibold">
            {q.numero}
          </span>
          <Textarea
            value={q.enonce}
            onChange={(e) => onChange({ ...q, enonce: e.target.value })}
            rows={2}
            placeholder="Énoncé de la question"
            aria-label={`Énoncé Q${q.numero}`}
          />
          <div className="flex items-center gap-1 shrink-0">
            <Input
              type="number"
              step="0.25"
              value={q.note_max}
              onChange={(e) => onChange({ ...q, note_max: Number(e.target.value) })}
              className="w-20 text-center font-mono"
              aria-label={`Points Q${q.numero}`}
            />
            <span className="text-xs text-muted">pts</span>
          </div>
        </div>
        <Textarea
          value={q.corrige}
          onChange={(e) => onChange({ ...q, corrige: e.target.value })}
          rows={2}
          placeholder="Réponse attendue (corrigé type)"
          aria-label={`Corrigé Q${q.numero}`}
        />
      </CardBody>
    </Card>
  );
}
