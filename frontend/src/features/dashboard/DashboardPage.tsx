import { useTranslation } from "react-i18next";
import { FileCheck2, Clock, Users, TrendingUp, Inbox } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardBody } from "@/components/ui/Card";
import { couleurNote } from "@/lib/utils";
import { StatCard } from "./StatCard";

// Données réelles branchées en Phase 3 (API) / Phase 5 (persistance).
// Tant qu'aucune correction n'existe, on affiche un état vide honnête.
interface CopieRecente {
  id: string;
  eleve: string;
  classe: string;
  note: number;
  max: number;
  valide: boolean;
}

const stats = { copies: 0, pending: 0, classes: 0, avg: 0 };
const recentes: CopieRecente[] = [];

export function DashboardPage() {
  const { t } = useTranslation();
  return (
    <>
      <PageHeader title={t("dashboard.title")} subtitle={t("dashboard.subtitle")} />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label={t("dashboard.copies")} value={stats.copies} icon={FileCheck2} delay={0} />
        <StatCard label={t("dashboard.pending")} value={stats.pending} icon={Clock} delay={0.05} />
        <StatCard label={t("dashboard.classes")} value={stats.classes} icon={Users} delay={0.1} />
        <StatCard
          label={t("dashboard.avg")}
          value={stats.avg ? stats.avg : "—"}
          suffix={stats.avg ? "/20" : undefined}
          icon={TrendingUp}
          delay={0.15}
        />
      </div>

      <Card className="mt-6">
        <CardBody>
          <h2 className="text-lg font-semibold text-ink mb-4">{t("dashboard.recent")}</h2>

          {recentes.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-3 py-14 text-center">
              <div className="grid h-14 w-14 place-items-center rounded-2xl bg-ink/6 text-muted">
                <Inbox size={26} />
              </div>
              <p className="text-sm font-medium text-ink">{t("dashboard.empty")}</p>
              <p className="text-sm text-muted">{t("dashboard.emptyHint")}</p>
            </div>
          ) : (
            <div className="space-y-2">
              {recentes.map((c) => (
                <div
                  key={c.id}
                  className="flex items-center gap-4 rounded-xl border border-line/70 px-4 py-3 hover:border-ink/20 transition-colors"
                >
                  <div className="grid h-9 w-9 place-items-center rounded-full bg-ink/8 text-ink text-sm font-semibold shrink-0">
                    {c.eleve.charAt(0)}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium text-ink">{c.eleve}</div>
                    <div className="text-xs text-muted">{c.classe}</div>
                  </div>
                  <span
                    className="font-mono text-sm font-semibold"
                    style={{ color: couleurNote(c.note, c.max) }}
                  >
                    {c.note} / {c.max}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>
    </>
  );
}
