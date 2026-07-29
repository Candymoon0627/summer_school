import { useEffect, useState } from "react";

import { getAuthHeader } from "./api";
import { AppLayout } from "./layout";
import { AdminUsersPage } from "./pages/AdminUsers";
import { AuditLogsPage } from "./pages/AuditLogs";
import { KnowledgePage } from "./pages/Knowledge";
import { LessonsPage } from "./pages/Lessons";
import { LoginPage } from "./pages/Login";
import { OperationsPage } from "./pages/Operations";
import { OverviewPage } from "./pages/Overview";
import { SchoolsPage } from "./pages/Schools";
import { SubmissionDetailPage } from "./pages/SubmissionDetail";
import { SubmissionsPage } from "./pages/Submissions";
import { useMe } from "./hooks";

export function App() {
  const [path, setPath] = useState(window.location.pathname);
  const [authHeader, setAuthHeader] = useState(getAuthHeader());

  useEffect(() => {
    const onPopState = () => setPath(window.location.pathname);
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const navigate = (nextPath: string) => {
    window.history.pushState(null, "", nextPath);
    setAuthHeader(getAuthHeader());
    setPath(nextPath);
  };

  const onLoggedIn = () => {
    setAuthHeader(getAuthHeader());
    navigate("/");
  };

  if (path === "/login") {
    return <LoginPage onLoggedIn={onLoggedIn} />;
  }
  if (!authHeader) {
    return <LoginPage onLoggedIn={onLoggedIn} />;
  }
  return <AuthenticatedApp path={path} navigate={navigate} />;
}

function AuthenticatedApp({ path, navigate }: { path: string; navigate: (path: string) => void }) {
  const me = useMe();
  return (
    <AppLayout currentPath={navigationPath(path)} navigate={navigate}>
      {renderPage(path, navigate, me.data)}
    </AppLayout>
  );
}

function renderPage(
  path: string,
  navigate: (path: string) => void,
  me?: { role: string; is_scoped: boolean },
) {
  if (path === "/") {
    return <OverviewPage />;
  }
  if (path === "/submissions") {
    return <SubmissionsPage navigate={navigate} />;
  }
  const submissionMatch = path.match(/^\/submissions\/([^/]+)$/);
  if (submissionMatch) {
    return <SubmissionDetailPage submissionId={submissionMatch[1]} navigate={navigate} />;
  }
  if (path === "/lessons") {
    return <LessonsPage />;
  }
  if (path === "/knowledge") {
    return <KnowledgePage />;
  }
  if (path === "/schools") {
    return <SchoolsPage />;
  }
  if (path === "/operations") {
    if (me?.is_scoped) {
      navigate("/");
      return null;
    }
    return <OperationsPage />;
  }
  if (path === "/admin-users") {
    if (me && me.role !== "super_admin") {
      navigate("/");
      return null;
    }
    return <AdminUsersPage />;
  }
  if (path === "/audit-logs") {
    return <AuditLogsPage />;
  }
  navigate("/");
  return null;
}

function navigationPath(path: string) {
  if (path.startsWith("/submissions")) {
    return "/submissions";
  }
  return path;
}
