import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  LayoutDashboard,
  FileText,
  PenLine,
  Share2,
  Users,
  Settings,
  type LucideIcon,
} from "lucide-react";
import { BalanceMark } from "@/components/brand/BalanceMark";
import { cn } from "@/lib/utils";

type NavItem = { to: string; key: string; icon: LucideIcon; end?: boolean };

const items: NavItem[] = [
  { to: "/", key: "dashboard", icon: LayoutDashboard, end: true },
  { to: "/devoirs", key: "devoirs", icon: FileText },
  { to: "/correction", key: "correction", icon: PenLine },
  { to: "/partage", key: "partage", icon: Share2 },
  { to: "/classes", key: "classes", icon: Users },
  { to: "/parametres", key: "settings", icon: Settings },
];

export function Sidebar() {
  const { t } = useTranslation();
  return (
    <aside className="hidden md:flex w-64 shrink-0 flex-col border-e border-line bg-surface/60 backdrop-blur">
      <div className="flex items-center gap-2.5 px-5 h-16 text-ink">
        <BalanceMark size={26} />
        <span className="font-display text-xl font-semibold">Mizan</span>
      </div>
      <nav className="flex-1 px-3 py-2 space-y-1">
        {items.map(({ to, key, icon: Icon, end }) => (
          <NavLink
            key={key}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-ink text-paper shadow-card"
                  : "text-muted-strong hover:bg-ink/5 hover:text-ink",
              )
            }
          >
            <Icon size={18} strokeWidth={2} />
            {t(`nav.${key}`)}
          </NavLink>
        ))}
      </nav>
      <div className="px-5 py-4 text-xs text-muted">v0.1 · MVP</div>
    </aside>
  );
}
