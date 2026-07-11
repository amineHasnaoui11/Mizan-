import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { DevoirsPage } from "@/features/devoirs/DevoirsPage";
import { CorrectionPage } from "@/features/correction/CorrectionPage";
import { PartagePage } from "@/features/partage/PartagePage";
import { ClassesPage } from "@/features/classes/ClassesPage";
import { SettingsPage } from "@/features/settings/SettingsPage";

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "devoirs", element: <DevoirsPage /> },
      { path: "correction", element: <CorrectionPage /> },
      { path: "partage", element: <PartagePage /> },
      { path: "classes", element: <ClassesPage /> },
      { path: "parametres", element: <SettingsPage /> },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
