import { lazy, Suspense, useEffect, useState } from "react";

import { Layout } from "./components/Layout";
import { clearTokens, getToken } from "./lib/api";
import { AuthPage } from "./pages/AuthPage";

const pages: Record<string, React.LazyExoticComponent<() => JSX.Element>> = {
  Dashboard: lazy(() => import("./pages/DashboardPage")),
  Websites: lazy(() => import("./pages/WebsitesPage")),
  Content: lazy(() => import("./pages/ContentPage")),
  "AI Studio": lazy(() => import("./pages/AIStudioPage")),
  Schedules: lazy(() => import("./pages/SchedulesPage")),
  Accounts: lazy(() => import("./pages/AccountsPage")),
  Analytics: lazy(() => import("./pages/AnalyticsPage")),
  Settings: lazy(() => import("./pages/SettingsPage")),
  Logs: lazy(() => import("./pages/LogsPage"))
};

export default function App() {
  const [authenticated, setAuthenticated] = useState(Boolean(getToken()));
  const [section, setSection] = useState("Dashboard");

  useEffect(() => {
    setAuthenticated(Boolean(getToken()));
    const onExpired = () => setAuthenticated(false);
    window.addEventListener("auth:expired", onExpired);
    return () => window.removeEventListener("auth:expired", onExpired);
  }, []);

  if (!authenticated) return <AuthPage onAuthenticated={() => setAuthenticated(true)} />;
  const Page = pages[section];

  return (
    <Layout
      section={section}
      setSection={setSection}
      onLogout={() => {
        clearTokens();
        setAuthenticated(false);
      }}
    >
      <Suspense fallback={<div className="rounded-lg border border-slate-200 bg-white p-5 text-sm text-slate-600">Loading module...</div>}>
        <Page />
      </Suspense>
    </Layout>
  );
}
