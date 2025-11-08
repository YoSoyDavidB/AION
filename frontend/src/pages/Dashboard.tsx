import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { MessageSquare, Database, FileText, Network } from "lucide-react";

export function Dashboard() {
  const stats = [
    {
      name: "Total Conversations",
      value: "12",
      icon: MessageSquare,
      description: "Active chats",
      trend: "+2 this week",
    },
    {
      name: "Memories Stored",
      value: "347",
      icon: Database,
      description: "Long-term memories",
      trend: "+23 this week",
    },
    {
      name: "Documents",
      value: "18",
      icon: FileText,
      description: "Knowledge base",
      trend: "+3 this week",
    },
    {
      name: "Graph Entities",
      value: "156",
      icon: Network,
      description: "Connected nodes",
      trend: "+15 this week",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.name}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.name}
              </CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground">
                {stat.description}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                {stat.trend}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>
            Your latest interactions with AION
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-start gap-4 border-b border-border pb-4 last:border-0 last:pb-0">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground">
                  <MessageSquare className="h-5 w-5" />
                </div>
                <div className="flex-1 space-y-1">
                  <p className="text-sm font-medium">
                    Chat conversation #{i}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Discussed project planning and task management
                  </p>
                  <p className="text-xs text-muted-foreground">
                    2 hours ago
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
