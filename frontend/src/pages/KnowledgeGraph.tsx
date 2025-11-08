import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function KnowledgeGraph() {
  return (
    <div className="h-full">
      <Card className="h-full flex flex-col">
        <CardHeader>
          <CardTitle>Knowledge Graph</CardTitle>
        </CardHeader>
        <CardContent className="flex-1 flex items-center justify-center">
          <p className="text-muted-foreground">
            Knowledge graph visualization coming soon...
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
