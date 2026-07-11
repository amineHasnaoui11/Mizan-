import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { LayoutDashboard, FileText, PenLine, Users, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

// Barre de navigation basse (mobile uniquement).
type NavItem = { to: string; key: string; icon: LucideIcon; end?: boolean };

const items: NavItem[] = [
  { to: "/", key: "dashboard", icon: LayoutDashboard, end: true },
  { to: "/devoirs", key: "devoirs", icon: FileText },
  { to: "/correction", key: "correction", icon: PenLine },
  { to: "/classes", key: "classes", icon: Users },
];

export function MobileNav() {
  const { t } = useTranslation();
  return (
    <nav className="md:hidden fixed inset-x-0 bottom-0 z-20 flex justify-around border-t border-line bg-surface/95 backdrop-blur px-2 py-1.5">
      {items.map(({ to, key, icon: Icon, end }) => (
        <NavLink
          key={key}
          to={to}
          end={end}
          className={({ isActive }) =>
            cn(
              "flex flex-col items-center gap-0.5 rounded-lg px-3 py-1.5 text-[11px] font-medium",
              isActive ? "text-ink" : "text-muted",
            )
          }
        >
          <Icon size={20} strokeWidth={2} />
          {t(`nav.${key}`)}
        </NavLink>
      ))}
    </nav>
  );
}
