import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Loader2,
  Save,
  RotateCcw,
  CheckCircle2,
  XCircle,
  FileText,
  Brain,
  MessageSquare,
  Tag,
  Users,
  Network,
} from "lucide-react";
import { promptsApi } from "@/lib/api/prompts";
import type { SystemPrompt } from "@/lib/api/prompts";

// Map prompt types to icons and friendly names
const promptTypeInfo: Record<string, { icon: any; name: string; color: string }> = {
  main_assistant: { icon: Brain, name: "Main Assistant", color: "text-blue-600" },
  memory_extraction: { icon: MessageSquare, name: "Memory Extraction", color: "text-purple-600" },
  summarization: { icon: FileText, name: "Summarization", color: "text-green-600" },
  intent_classification: { icon: Tag, name: "Intent Classification", color: "text-orange-600" },
  entity_description: { icon: Users, name: "Entity Description", color: "text-pink-600" },
  entity_extraction: { icon: Users, name: "Entity Extraction", color: "text-indigo-600" },
  relationship_extraction: { icon: Network, name: "Relationship Extraction", color: "text-cyan-600" },
  rag_system: { icon: Brain, name: "RAG System", color: "text-red-600" },
};

interface EditingPrompt {
  promptType: string;
  content: string;
  description: string;
}

export function Prompts() {
  const queryClient = useQueryClient();
  const [editingPrompt, setEditingPrompt] = useState<EditingPrompt | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Fetch all prompts
  const { data: promptsData, isLoading } = useQuery({
    queryKey: ["prompts"],
    queryFn: () => promptsApi.listPrompts(),
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ promptType, content, description }: EditingPrompt) =>
      promptsApi.updatePrompt(promptType, { content, description }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["prompts"] });
      setEditingPrompt(null);
      setSuccessMessage(`${promptTypeInfo[data.prompt_type]?.name || data.prompt_type} updated successfully`);
      setTimeout(() => setSuccessMessage(null), 3000);
    },
  });

  // Reset mutation
  const resetMutation = useMutation({
    mutationFn: (promptType: string) => promptsApi.resetPrompt(promptType),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["prompts"] });
      if (editingPrompt?.promptType === data.prompt_type) {
        setEditingPrompt(null);
      }
      setSuccessMessage(`${promptTypeInfo[data.prompt_type]?.name || data.prompt_type} reset to default`);
      setTimeout(() => setSuccessMessage(null), 3000);
    },
  });

  const handleEdit = (prompt: SystemPrompt) => {
    setEditingPrompt({
      promptType: prompt.prompt_type,
      content: prompt.content,
      description: prompt.description,
    });
  };

  const handleSave = () => {
    if (editingPrompt) {
      updateMutation.mutate(editingPrompt);
    }
  };

  const handleCancel = () => {
    setEditingPrompt(null);
  };

  const handleReset = (promptType: string) => {
    if (confirm("Are you sure you want to reset this prompt to its default value?")) {
      resetMutation.mutate(promptType);
    }
  };

  return (
    <div className="h-full space-y-6 p-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">System Prompts</h2>
        <p className="text-muted-foreground">
          Manage and customize the prompts used by AION's AI system
        </p>
      </div>

      {/* Success Message */}
      {successMessage && (
        <Alert className="border-green-600 bg-green-50">
          <CheckCircle2 className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-900">{successMessage}</AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Prompts List */}
      {promptsData && (
        <div className="space-y-4">
          {promptsData.prompts.map((prompt) => {
            const isEditing = editingPrompt?.promptType === prompt.prompt_type;
            const info = promptTypeInfo[prompt.prompt_type] || {
              icon: FileText,
              name: prompt.prompt_type,
              color: "text-gray-600",
            };
            const Icon = info.icon;

            return (
              <Card key={prompt.prompt_type}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <Icon className={`h-5 w-5 ${info.color}`} />
                      <div>
                        <CardTitle>{info.name}</CardTitle>
                        <CardDescription className="mt-1">
                          {isEditing ? (
                            <Input
                              value={editingPrompt.description}
                              onChange={(e) =>
                                setEditingPrompt({ ...editingPrompt, description: e.target.value })
                              }
                              placeholder="Prompt description"
                              className="mt-2"
                            />
                          ) : (
                            prompt.description
                          )}
                        </CardDescription>
                      </div>
                    </div>
                    {!isEditing && (
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEdit(prompt)}
                        >
                          Edit
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleReset(prompt.prompt_type)}
                          disabled={resetMutation.isPending}
                        >
                          {resetMutation.isPending ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <RotateCcw className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  {isEditing ? (
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="content">Prompt Content</Label>
                        <Textarea
                          id="content"
                          value={editingPrompt.content}
                          onChange={(e) =>
                            setEditingPrompt({ ...editingPrompt, content: e.target.value })
                          }
                          rows={12}
                          className="mt-2 font-mono text-sm"
                          placeholder="Enter prompt content..."
                        />
                      </div>
                      <div className="flex gap-2">
                        <Button
                          onClick={handleSave}
                          disabled={updateMutation.isPending || !editingPrompt.content.trim()}
                        >
                          {updateMutation.isPending ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              Saving...
                            </>
                          ) : (
                            <>
                              <Save className="mr-2 h-4 w-4" />
                              Save Changes
                            </>
                          )}
                        </Button>
                        <Button
                          variant="outline"
                          onClick={handleCancel}
                          disabled={updateMutation.isPending}
                        >
                          Cancel
                        </Button>
                      </div>
                      {updateMutation.isError && (
                        <Alert variant="destructive">
                          <XCircle className="h-4 w-4" />
                          <AlertDescription>
                            Failed to update prompt: {(updateMutation.error as Error).message}
                          </AlertDescription>
                        </Alert>
                      )}
                    </div>
                  ) : (
                    <div className="relative">
                      <pre className="whitespace-pre-wrap rounded-lg bg-muted p-4 text-sm font-mono max-h-48 overflow-y-auto">
                        {prompt.content}
                      </pre>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Help Text */}
      <Card>
        <CardHeader>
          <CardTitle>About System Prompts</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-start gap-2">
              <span className="mt-1">•</span>
              <span>
                System prompts control how AION behaves in different contexts
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1">•</span>
              <span>
                Changes take effect immediately and are cached for performance
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1">•</span>
              <span>
                Use the reset button to restore a prompt to its default value
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1">•</span>
              <span>
                Be careful when editing prompts as they directly affect AI behavior
              </span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
