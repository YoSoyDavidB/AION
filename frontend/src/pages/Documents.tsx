import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function Documents() {
  return (
    <div className="h-full">
      <Card className="h-full flex flex-col">
        <CardHeader>
          <CardTitle>Document Management</CardTitle>
        </CardHeader>
        <CardContent className="flex-1 flex items-center justify-center">
          <p className="text-muted-foreground">
            Document management interface coming soon...
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
