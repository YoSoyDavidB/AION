import { NavLink } from "react-router-dom";
import {
  MessageSquare,
  Database,
  FileText,
  Network,
  LayoutDashboard,
  Settings,
  Wand2,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Chat", href: "/chat", icon: MessageSquare },
  { name: "Memories", href: "/memories", icon: Database },
  { name: "Documents", href: "/documents", icon: FileText },
  { name: "Knowledge Graph", href: "/knowledge-graph", icon: Network },
  { name: "Prompts", href: "/prompts", icon: Wand2 },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  return (
    <div className="flex h-full w-64 flex-col bg-card border-r border-border">
      {/* Logo */}
      <div className="flex h-16 items-center gap-2 border-b border-border px-6">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <MessageSquare className="h-6 w-6" />
        </div>
        <div>
          <h1 className="text-xl font-bold">AION</h1>
          <p className="text-xs text-muted-foreground">AI Assistant</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-4">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )
            }
          >
            <item.icon className="h-5 w-5" />
            {item.name}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-border p-4">
        <div className="flex items-center gap-3 rounded-lg bg-muted px-3 py-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
            D
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">David</p>
            <p className="text-xs text-muted-foreground truncate">
              {import.meta.env.VITE_DEFAULT_USER_ID}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
