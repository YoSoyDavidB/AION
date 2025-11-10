import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "./components/theme-provider";
import { AppLayout } from "./components/layout/AppLayout";
import { Dashboard } from "./pages/Dashboard";
import { Chat } from "./pages/Chat";
import { Memories } from "./pages/Memories";
import { Documents } from "./pages/Documents";
import { KnowledgeGraph } from "./pages/KnowledgeGraph";
import { Settings } from "./pages/Settings";
import { Prompts } from "./pages/Prompts";

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="aion-ui-theme">
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<AppLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="chat" element={<Chat />} />
              <Route path="memories" element={<Memories />} />
              <Route path="documents" element={<Documents />} />
              <Route path="knowledge-graph" element={<KnowledgeGraph />} />
              <Route path="prompts" element={<Prompts />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  );
}

export default App;
