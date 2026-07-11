import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { MobileNav } from "./MobileNav";

export function AppShell() {
  return (
    <div className="flex min-h-screen bg-paper">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />
        <main className="flex-1 px-4 sm:px-6 lg:px-8 py-6 pb-24 md:pb-6">
          <div className="mx-auto w-full max-w-6xl animate-fade-up">
            <Outlet />
          </div>
        </main>
        <MobileNav />
      </div>
    </div>
  );
}
