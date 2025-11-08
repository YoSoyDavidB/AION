import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { memoriesApi } from "@/lib/api/memories";
import type { Memory, MemoryType, SensitivityLevel } from "@/lib/types/memory";
import {
  Search,
  Plus,
  Trash2,
  Eye,
  Brain,
  AlertCircle,
  Calendar,
  Hash,
} from "lucide-react";

const MEMORY_TYPES: MemoryType[] = ["preference", "fact", "task", "goal", "profile"];
const SENSITIVITY_LEVELS: SensitivityLevel[] = ["low", "medium", "high"];

const MEMORY_TYPE_COLORS: Record<MemoryType, string> = {
  preference: "bg-blue-500",
  fact: "bg-green-500",
  task: "bg-yellow-500",
  goal: "bg-purple-500",
  profile: "bg-pink-500",
};

const SENSITIVITY_COLORS: Record<SensitivityLevel, string> = {
  low: "bg-gray-500",
  medium: "bg-orange-500",
  high: "bg-red-500",
};

export function Memories() {
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<MemoryType | "all">("all");
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isDetailDialogOpen, setIsDetailDialogOpen] = useState(false);

  // Form state for creating/editing memories
  const [formData, setFormData] = useState({
    short_text: "",
    memory_type: "fact" as MemoryType,
    sensitivity: "medium" as SensitivityLevel,
  });

  const queryClient = useQueryClient();
  const userId = import.meta.env.VITE_DEFAULT_USER_ID || "david";

  // Fetch all memories
  const { data: memories, isLoading } = useQuery({
    queryKey: ["memories", userId],
    queryFn: () => memoriesApi.getUserMemories(userId, 100),
  });

  // Search memories
  const { data: searchResults, refetch: refetchSearch } = useQuery({
    queryKey: ["memories-search", userId, searchQuery],
    queryFn: () => memoriesApi.searchMemories(userId, searchQuery, 20),
    enabled: false,
  });

  // Create memory mutation
  const createMemoryMutation = useMutation({
    mutationFn: (data: {
      short_text: string;
      memory_type: MemoryType;
      sensitivity: SensitivityLevel;
    }) =>
      memoriesApi.createMemory({
        user_id: userId,
        ...data,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["memories"] });
      setIsCreateDialogOpen(false);
      setFormData({
        short_text: "",
        memory_type: "fact",
        sensitivity: "medium",
      });
    },
  });

  // Delete memory mutation
  const deleteMemoryMutation = useMutation({
    mutationFn: (memoryId: string) => memoriesApi.deleteMemory(userId, memoryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["memories"] });
      setIsDetailDialogOpen(false);
    },
  });

  const handleSearch = () => {
    if (searchQuery.trim()) {
      refetchSearch();
    }
  };

  const handleCreateMemory = () => {
    if (formData.short_text.trim()) {
      createMemoryMutation.mutate(formData);
    }
  };

  const handleDeleteMemory = () => {
    if (selectedMemory) {
      deleteMemoryMutation.mutate(selectedMemory.memory_id);
    }
  };

  // Filter memories
  const displayMemories = searchQuery && searchResults ? searchResults : memories;
  const filteredMemories =
    typeFilter === "all"
      ? displayMemories
      : displayMemories?.filter((m) => m.memory_type === typeFilter);

  // Calculate stats
  const stats = {
    total: memories?.length || 0,
    byType: MEMORY_TYPES.reduce((acc, type) => {
      acc[type] = memories?.filter((m) => m.memory_type === type).length || 0;
      return acc;
    }, {} as Record<MemoryType, number>),
  };

  return (
    <div className="h-full space-y-4">
      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Memories</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>

        {MEMORY_TYPES.map((type) => (
          <Card key={type}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium capitalize">{type}</CardTitle>
              <div className={`h-3 w-3 rounded-full ${MEMORY_TYPE_COLORS[type]}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.byType[type]}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Content */}
      <Card className="flex-1">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Memory Management</CardTitle>
            <Button onClick={() => setIsCreateDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Create Memory
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Filters and Search */}
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search memories by semantic similarity..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  className="pl-9"
                />
              </div>
            </div>
            <Button onClick={handleSearch} variant="outline">
              Search
            </Button>
            <Select
              value={typeFilter}
              onValueChange={(value) => setTypeFilter(value as MemoryType | "all")}
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {MEMORY_TYPES.map((type) => (
                  <SelectItem key={type} value={type}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Memories List */}
          <ScrollArea className="h-[500px]">
            {isLoading ? (
              <div className="flex items-center justify-center h-40">
                <p className="text-muted-foreground">Loading memories...</p>
              </div>
            ) : filteredMemories && filteredMemories.length > 0 ? (
              <div className="space-y-2">
                {filteredMemories.map((memory) => (
                  <div
                    key={memory.memory_id}
                    className="flex items-start gap-4 p-4 border rounded-lg hover:bg-accent cursor-pointer transition-colors"
                    onClick={() => {
                      setSelectedMemory(memory);
                      setIsDetailDialogOpen(true);
                    }}
                  >
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2">
                        <Badge className={MEMORY_TYPE_COLORS[memory.memory_type]}>
                          {memory.memory_type}
                        </Badge>
                        <Badge variant="outline" className={SENSITIVITY_COLORS[memory.sensitivity]}>
                          {memory.sensitivity}
                        </Badge>
                      </div>
                      <p className="text-sm">{memory.short_text}</p>
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {new Date(memory.created_at).toLocaleDateString()}
                        </span>
                        <span className="flex items-center gap-1">
                          <Hash className="h-3 w-3" />
                          Referenced {memory.num_times_referenced} times
                        </span>
                        <span>Relevance: {(memory.relevance_score * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedMemory(memory);
                        setIsDetailDialogOpen(true);
                      }}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-40 text-center">
                <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No memories found</p>
                <p className="text-sm text-muted-foreground">
                  Try adjusting your filters or create a new memory
                </p>
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Create Memory Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Memory</DialogTitle>
            <DialogDescription>
              Add a new memory to your long-term knowledge base
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="memory-text">Memory Text</Label>
              <Textarea
                id="memory-text"
                placeholder="Enter memory content..."
                value={formData.short_text}
                onChange={(e) =>
                  setFormData({ ...formData, short_text: e.target.value })
                }
                rows={4}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="memory-type">Type</Label>
                <Select
                  value={formData.memory_type}
                  onValueChange={(value) =>
                    setFormData({ ...formData, memory_type: value as MemoryType })
                  }
                >
                  <SelectTrigger id="memory-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {MEMORY_TYPES.map((type) => (
                      <SelectItem key={type} value={type}>
                        {type.charAt(0).toUpperCase() + type.slice(1)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="sensitivity">Sensitivity</Label>
                <Select
                  value={formData.sensitivity}
                  onValueChange={(value) =>
                    setFormData({ ...formData, sensitivity: value as SensitivityLevel })
                  }
                >
                  <SelectTrigger id="sensitivity">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {SENSITIVITY_LEVELS.map((level) => (
                      <SelectItem key={level} value={level}>
                        {level.charAt(0).toUpperCase() + level.slice(1)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateMemory}
              disabled={!formData.short_text.trim() || createMemoryMutation.isPending}
            >
              {createMemoryMutation.isPending ? "Creating..." : "Create Memory"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Memory Detail Dialog */}
      <Dialog open={isDetailDialogOpen} onOpenChange={setIsDetailDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Memory Details</DialogTitle>
          </DialogHeader>
          {selectedMemory && (
            <div className="space-y-4">
              <div className="flex gap-2">
                <Badge className={MEMORY_TYPE_COLORS[selectedMemory.memory_type]}>
                  {selectedMemory.memory_type}
                </Badge>
                <Badge variant="outline" className={SENSITIVITY_COLORS[selectedMemory.sensitivity]}>
                  {selectedMemory.sensitivity}
                </Badge>
              </div>
              <div>
                <Label>Content</Label>
                <p className="text-sm mt-2">{selectedMemory.short_text}</p>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <Label>Created</Label>
                  <p className="text-muted-foreground mt-1">
                    {new Date(selectedMemory.created_at).toLocaleString()}
                  </p>
                </div>
                <div>
                  <Label>Last Referenced</Label>
                  <p className="text-muted-foreground mt-1">
                    {new Date(selectedMemory.last_referenced_at).toLocaleString()}
                  </p>
                </div>
                <div>
                  <Label>Times Referenced</Label>
                  <p className="text-muted-foreground mt-1">
                    {selectedMemory.num_times_referenced}
                  </p>
                </div>
                <div>
                  <Label>Relevance Score</Label>
                  <p className="text-muted-foreground mt-1">
                    {(selectedMemory.relevance_score * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="col-span-2">
                  <Label>Source</Label>
                  <p className="text-muted-foreground mt-1">{selectedMemory.source}</p>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button
              variant="destructive"
              onClick={handleDeleteMemory}
              disabled={deleteMemoryMutation.isPending}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              {deleteMemoryMutation.isPending ? "Deleting..." : "Delete"}
            </Button>
            <Button variant="outline" onClick={() => setIsDetailDialogOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
