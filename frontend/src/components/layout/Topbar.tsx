import { useTranslation } from "react-i18next";
import { Languages } from "lucide-react";
import { appliquerDirection, LANGS, type Lang } from "@/lib/i18n";
import { BalanceMark } from "@/components/brand/BalanceMark";
import { cn } from "@/lib/utils";

export function Topbar() {
  const { i18n, t } = useTranslation();
  const lang = i18n.language as Lang;

  function changer(l: Lang) {
    i18n.changeLanguage(l);
    appliquerDirection(l);
  }

  return (
    <header className="sticky top-0 z-10 flex items-center justify-between gap-4 h-16 px-5 border-b border-line bg-paper/80 backdrop-blur">
      <div className="flex items-center gap-2 md:hidden text-ink">
        <BalanceMark size={22} animate={false} />
        <span className="font-display text-lg font-semibold">Mizan</span>
      </div>
      <p className="hidden md:block text-sm text-muted">{t("app.tagline")}</p>

      <div className="flex items-center gap-3">
        <div className="flex items-center rounded-full border border-line bg-surface p-0.5" role="group" aria-label="Langue">
          <Languages size={15} className="mx-1.5 text-muted" aria-hidden />
          {LANGS.map((l) => (
            <button
              key={l}
              onClick={() => changer(l)}
              className={cn(
                "rounded-full px-2.5 py-1 text-xs font-semibold uppercase transition-colors",
                lang === l ? "bg-ink text-paper" : "text-muted hover:text-ink",
              )}
              aria-pressed={lang === l}
            >
              {l}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <div
            className="grid h-9 w-9 place-items-center rounded-full bg-accent/15 text-accent-deep font-semibold text-sm"
            aria-hidden
          >
            N
          </div>
          <span className="hidden sm:block text-sm font-medium text-ink">Mme Nourra</span>
        </div>
      </div>
    </header>
  );
}
