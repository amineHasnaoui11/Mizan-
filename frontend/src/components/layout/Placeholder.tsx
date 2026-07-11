import { useTranslation } from "react-i18next";
import type { LucideIcon } from "lucide-react";
import { PageHeader } from "./PageHeader";
import { Card, CardBody } from "@/components/ui/Card";

/** Écran neutre stylé pour les features en cours de construction (Phases 1→5). */
export function Placeholder({
  titleKey,
  subtitleKey,
  icon: Icon,
}: {
  titleKey: string;
  subtitleKey: string;
  icon: LucideIcon;
}) {
  const { t } = useTranslation();
  return (
    <>
      <PageHeader title={t(titleKey)} subtitle={t(subtitleKey)} />
      <Card>
        <CardBody className="flex flex-col items-center justify-center gap-3 py-16 text-center">
          <div className="grid h-14 w-14 place-items-center rounded-2xl bg-accent/12 text-accent-deep">
            <Icon size={26} />
          </div>
          <p className="text-sm text-muted">{t("common.soon")}</p>
        </CardBody>
      </Card>
    </>
  );
}
