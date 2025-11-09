import { Outlet, useLocation } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";

const pageInfo: Record<string, { title: string; subtitle?: string }> = {
  "/": {
    title: "Dashboard",
    subtitle: "Overview of your AI assistant",
  },
  "/chat": {
    title: "Chat",
    subtitle: "Conversation with AION",
  },
  "/memories": {
    title: "Memories",
    subtitle: "Manage your long-term memories",
  },
  "/documents": {
    title: "Documents",
    subtitle: "Your knowledge base",
  },
  "/knowledge-graph": {
    title: "Knowledge Graph",
    subtitle: "Visualize entity relationships",
  },
  "/prompts": {
    title: "System Prompts",
    subtitle: "Customize AI behavior",
  },
  "/settings": {
    title: "Settings",
    subtitle: "Configure your preferences",
  },
};

export function AppLayout() {
  const location = useLocation();
  const currentPage = pageInfo[location.pathname] || {
    title: "AION",
    subtitle: "",
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header title={currentPage.title} subtitle={currentPage.subtitle} />

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
