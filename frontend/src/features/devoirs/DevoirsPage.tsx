import { useState } from "react";
import { Plus, FileText, Trash2, Inbox } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardBody } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { listDevoirs, deleteDevoir, type DevoirStocke } from "@/lib/devoirsStore";
import { NouveauDevoir } from "./NouveauDevoir";

export function DevoirsPage() {
  const [creation, setCreation] = useState(false);
  const [devoirs, setDevoirs] = useState<DevoirStocke[]>(() => listDevoirs());

  function rafraichir() {
    setDevoirs(listDevoirs());
  }

  if (creation) {
    return (
      <NouveauDevoir
        onCancel={() => setCreation(false)}
        onDone={() => {
          setCreation(false);
          rafraichir();
        }}
      />
    );
  }

  return (
    <>
      <PageHeader
        title="Devoirs"
        subtitle="Barème et corrigé type par devoir"
        action={
          <Button variant="accent" onClick={() => setCreation(true)}>
            <Plus size={18} /> Nouveau devoir
          </Button>
        }
      />

      {devoirs.length === 0 ? (
        <Card>
          <CardBody className="flex flex-col items-center justify-center gap-3 py-16 text-center">
            <div className="grid h-14 w-14 place-items-center rounded-2xl bg-ink/6 text-muted">
              <Inbox size={26} />
            </div>
            <p className="text-sm font-medium text-ink">Aucun devoir pour l'instant</p>
            <p className="text-sm text-muted">
              Crée un devoir en déposant ton barème, ton devoir vierge et ta correction.
            </p>
            <Button variant="accent" onClick={() => setCreation(true)} className="mt-1">
              <Plus size={18} /> Nouveau devoir
            </Button>
          </CardBody>
        </Card>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {devoirs.map((d) => (
            <Card key={d.devoir_id} className="hover:shadow-lift transition-shadow">
              <CardBody className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="grid h-10 w-10 place-items-center rounded-xl bg-ink/8 text-ink">
                    <FileText size={20} />
                  </div>
                  <button
                    onClick={() => {
                      deleteDevoir(d.devoir_id);
                      rafraichir();
                    }}
                    className="text-muted hover:text-score-zero"
                    aria-label="Supprimer"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
                <div>
                  <h3 className="font-semibold text-ink">{d.matiere || d.devoir_id}</h3>
                  <p className="text-xs text-muted">{d.niveau}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge>{d.questions.length} questions</Badge>
                  <Badge>
                    <span className="font-mono">{d.note_max_devoir}</span>&nbsp;pts
                  </Badge>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </>
  );
}
