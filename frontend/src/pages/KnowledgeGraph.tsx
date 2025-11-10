import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { LoadingSpinner } from "@/components/ui/spinner";
import { SkeletonCard } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { entitiesApi } from "@/lib/api/entities";
import type { Entity, EntityGraph } from "@/lib/types/entity";
import { EntityType } from "@/lib/types/entity";
import {
  Search,
  Users,
  Building2,
  Lightbulb,
  FolderOpen,
  Calendar,
  MapPin,
  FileText,
  AlertCircle,
  Network,
  ArrowRight,
  Filter,
  X,
} from "lucide-react";

const entityTypeIcons: Record<EntityType, React.ComponentType<{ className?: string }>> = {
  [EntityType.PERSON]: Users,
  [EntityType.ORGANIZATION]: Building2,
  [EntityType.CONCEPT]: Lightbulb,
  [EntityType.PROJECT]: FolderOpen,
  [EntityType.EVENT]: Calendar,
  [EntityType.LOCATION]: MapPin,
  [EntityType.DOCUMENT]: FileText,
};

const entityTypeLabels: Record<EntityType, string> = {
  [EntityType.PERSON]: "People",
  [EntityType.ORGANIZATION]: "Organizations",
  [EntityType.CONCEPT]: "Concepts",
  [EntityType.PROJECT]: "Projects",
  [EntityType.EVENT]: "Events",
  [EntityType.LOCATION]: "Locations",
  [EntityType.DOCUMENT]: "Documents",
};

const relationshipTypeLabels: Record<string, string> = {
  works_on: "Works on",
  collaborated_with: "Collaborated with",
  manages: "Manages",
  part_of: "Part of",
  related_to: "Related to",
  mentioned_in: "Mentioned in",
  located_at: "Located at",
  occurred_at: "Occurred at",
};

export function KnowledgeGraph() {
  const [selectedType, setSelectedType] = useState<EntityType | "all">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [isDetailDialogOpen, setIsDetailDialogOpen] = useState(false);

  // Fetch all entity types
  const personQuery = useQuery({
    queryKey: ["entities", EntityType.PERSON],
    queryFn: () => entitiesApi.getEntitiesByType(EntityType.PERSON),
  });

  const organizationQuery = useQuery({
    queryKey: ["entities", EntityType.ORGANIZATION],
    queryFn: () => entitiesApi.getEntitiesByType(EntityType.ORGANIZATION),
  });

  const conceptQuery = useQuery({
    queryKey: ["entities", EntityType.CONCEPT],
    queryFn: () => entitiesApi.getEntitiesByType(EntityType.CONCEPT),
  });

  const projectQuery = useQuery({
    queryKey: ["entities", EntityType.PROJECT],
    queryFn: () => entitiesApi.getEntitiesByType(EntityType.PROJECT),
  });

  const eventQuery = useQuery({
    queryKey: ["entities", EntityType.EVENT],
    queryFn: () => entitiesApi.getEntitiesByType(EntityType.EVENT),
  });

  const locationQuery = useQuery({
    queryKey: ["entities", EntityType.LOCATION],
    queryFn: () => entitiesApi.getEntitiesByType(EntityType.LOCATION),
  });

  const documentQuery = useQuery({
    queryKey: ["entities", EntityType.DOCUMENT],
    queryFn: () => entitiesApi.getEntitiesByType(EntityType.DOCUMENT),
  });

  // Fetch entity graph when entity is selected
  const { data: entityGraph } = useQuery({
    queryKey: ["entity-graph", selectedEntity?.entity_id],
    queryFn: () => entitiesApi.getEntityGraph(selectedEntity!.entity_id),
    enabled: !!selectedEntity && isDetailDialogOpen,
  });

  // Combine all entities
  const allEntities: Entity[] = [
    ...(personQuery.data || []),
    ...(organizationQuery.data || []),
    ...(conceptQuery.data || []),
    ...(projectQuery.data || []),
    ...(eventQuery.data || []),
    ...(locationQuery.data || []),
    ...(documentQuery.data || []),
  ];

  // Filter entities
  const filteredEntities = allEntities.filter((entity) => {
    const matchesType = selectedType === "all" || entity.entity_type === selectedType;
    const matchesSearch =
      !searchQuery ||
      entity.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      entity.description?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesType && matchesSearch;
  });

  // Calculate stats
  const stats = {
    [EntityType.PERSON]: personQuery.data?.length || 0,
    [EntityType.ORGANIZATION]: organizationQuery.data?.length || 0,
    [EntityType.CONCEPT]: conceptQuery.data?.length || 0,
    [EntityType.PROJECT]: projectQuery.data?.length || 0,
    [EntityType.EVENT]: eventQuery.data?.length || 0,
    [EntityType.LOCATION]: locationQuery.data?.length || 0,
    [EntityType.DOCUMENT]: documentQuery.data?.length || 0,
  };

  const totalEntities = Object.values(stats).reduce((sum, count) => sum + count, 0);

  const isLoading =
    personQuery.isLoading ||
    organizationQuery.isLoading ||
    conceptQuery.isLoading ||
    projectQuery.isLoading ||
    eventQuery.isLoading ||
    locationQuery.isLoading ||
    documentQuery.isLoading;

  return (
    <div className="h-full space-y-4">
      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4 lg:grid-cols-7">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total</CardTitle>
            <Network className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalEntities}</div>
          </CardContent>
        </Card>

        {Object.entries(entityTypeLabels).map(([type, label]) => {
          const Icon = entityTypeIcons[type as EntityType];
          return (
            <Card key={type}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{label}</CardTitle>
                <Icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats[type as EntityType]}</div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Main Content */}
      <Card className="flex-1">
        <CardHeader>
          <CardTitle>Knowledge Graph</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Filters */}
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search entities..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
            <Select
              value={selectedType}
              onValueChange={(value) => setSelectedType(value as EntityType | "all")}
            >
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {Object.entries(entityTypeLabels).map(([type, label]) => (
                  <SelectItem key={type} value={type}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Results Count */}
          {!isLoading && (
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>
                Showing {filteredEntities.length} of {allEntities.length} entities
              </span>
              {(searchQuery || selectedType !== "all") && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setSearchQuery("");
                    setSelectedType("all");
                  }}
                >
                  <X className="h-4 w-4 mr-2" />
                  Clear filters
                </Button>
              )}
            </div>
          )}

          {/* Entities List */}
          <ScrollArea className="h-[500px]">
            {isLoading ? (
              <div className="space-y-4">
                {[1, 2, 3, 4].map((i) => (
                  <SkeletonCard key={i} />
                ))}
              </div>
            ) : filteredEntities.length > 0 ? (
              <div className="space-y-2">
                {filteredEntities.map((entity) => {
                  const Icon = entityTypeIcons[entity.entity_type];
                  return (
                    <div
                      key={entity.entity_id}
                      className="flex items-start gap-4 p-4 border rounded-lg hover:bg-accent cursor-pointer transition-colors"
                      onClick={() => {
                        setSelectedEntity(entity);
                        setIsDetailDialogOpen(true);
                      }}
                    >
                      <div className="mt-1">
                        <Icon className="h-5 w-5 text-muted-foreground" />
                      </div>
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium">{entity.name}</h3>
                          <Badge variant="secondary">
                            {entityTypeLabels[entity.entity_type]}
                          </Badge>
                        </div>
                        {entity.description && (
                          <p className="text-sm text-muted-foreground line-clamp-2">
                            {entity.description}
                          </p>
                        )}
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <span>
                            Updated: {new Date(entity.updated_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <EmptyState
                icon={searchQuery || selectedType !== "all" ? Search : Network}
                title={searchQuery || selectedType !== "all" ? "No entities found" : "No entities yet"}
                description={
                  searchQuery || selectedType !== "all"
                    ? "Try adjusting your search or filter criteria"
                    : "Entities will appear here as conversations are processed"
                }
                action={
                  searchQuery || selectedType !== "all"
                    ? {
                        label: "Clear filters",
                        onClick: () => {
                          setSearchQuery("");
                          setSelectedType("all");
                        },
                      }
                    : undefined
                }
              />
            )}
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Entity Detail Dialog */}
      <Dialog open={isDetailDialogOpen} onOpenChange={setIsDetailDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Entity Details</DialogTitle>
            <DialogDescription>
              View entity information and relationships
            </DialogDescription>
          </DialogHeader>
          {selectedEntity && (
            <div className="space-y-6">
              {/* Entity Info */}
              <div className="space-y-4">
                <div>
                  <Label>Name</Label>
                  <div className="flex items-center gap-2 mt-2">
                    {(() => {
                      const Icon = entityTypeIcons[selectedEntity.entity_type];
                      return <Icon className="h-5 w-5 text-muted-foreground" />;
                    })()}
                    <p className="text-lg font-medium">{selectedEntity.name}</p>
                    <Badge variant="secondary">
                      {entityTypeLabels[selectedEntity.entity_type]}
                    </Badge>
                  </div>
                </div>

                {selectedEntity.description && (
                  <div>
                    <Label>Description</Label>
                    <p className="text-sm mt-2 text-muted-foreground">
                      {selectedEntity.description}
                    </p>
                  </div>
                )}

                {Object.keys(selectedEntity.properties).length > 0 && (
                  <div>
                    <Label>Properties</Label>
                    <div className="mt-2 space-y-2">
                      {Object.entries(selectedEntity.properties).map(([key, value]) => (
                        <div
                          key={key}
                          className="flex items-start gap-2 text-sm p-2 bg-muted rounded"
                        >
                          <span className="font-medium min-w-[120px]">{key}:</span>
                          <span className="text-muted-foreground">
                            {Array.isArray(value) ? value.join(", ") : String(value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <Label>Created</Label>
                    <p className="text-muted-foreground mt-1">
                      {new Date(selectedEntity.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <Label>Updated</Label>
                    <p className="text-muted-foreground mt-1">
                      {new Date(selectedEntity.updated_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>

              {/* Relationships */}
              {entityGraph && entityGraph.relationships.length > 0 && (
                <div>
                  <Label className="text-base">
                    Relationships ({entityGraph.relationships.length})
                  </Label>
                  <div className="mt-3 space-y-2">
                    {entityGraph.relationships.map((rel) => {
                      const isSource =
                        rel.source_entity.entity_id === selectedEntity.entity_id;
                      const relatedEntity = isSource
                        ? rel.target_entity
                        : rel.source_entity;
                      const Icon = entityTypeIcons[relatedEntity.entity_type];

                      return (
                        <div
                          key={rel.relationship_id}
                          className="p-3 border rounded-lg space-y-2"
                        >
                          <div className="flex items-center gap-2">
                            <Icon className="h-4 w-4 text-muted-foreground" />
                            <span className="font-medium">{relatedEntity.name}</span>
                            <Badge variant="outline" className="ml-auto">
                              {relationshipTypeLabels[rel.relationship_type] ||
                                rel.relationship_type}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <span>{selectedEntity.name}</span>
                            <ArrowRight className="h-3 w-3" />
                            <span>{relatedEntity.name}</span>
                            <span className="ml-auto">
                              Strength: {(rel.strength * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Related Entities */}
              {entityGraph && entityGraph.related_entities.length > 0 && (
                <div>
                  <Label className="text-base">
                    Related Entities ({entityGraph.related_entities.length})
                  </Label>
                  <div className="mt-3 grid grid-cols-2 gap-2">
                    {entityGraph.related_entities.map((entity) => {
                      const Icon = entityTypeIcons[entity.entity_type];
                      return (
                        <div
                          key={entity.entity_id}
                          className="flex items-center gap-2 p-2 border rounded text-sm"
                        >
                          <Icon className="h-4 w-4 text-muted-foreground" />
                          <span className="flex-1 truncate">{entity.name}</span>
                          <Badge variant="secondary" className="text-xs">
                            {entityTypeLabels[entity.entity_type]}
                          </Badge>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
          <div className="flex justify-end">
            <Button variant="outline" onClick={() => setIsDetailDialogOpen(false)}>
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
