import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { documentsApi } from "@/lib/api/documents";
import type { Document } from "@/lib/types/document";
import {
  Search,
  Upload,
  Trash2,
  Eye,
  FileText,
  AlertCircle,
  Calendar,
  FileCode,
} from "lucide-react";

export function KnowledgeBase() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false);
  const [isDetailDialogOpen, setIsDetailDialogOpen] = useState(false);

  // Upload form state
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadTags, setUploadTags] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const queryClient = useQueryClient();
  const userId = import.meta.env.VITE_DEFAULT_USER_ID || "david";

  // Fetch all documents
  const { data: documents, isLoading } = useQuery({
    queryKey: ["documents", userId],
    queryFn: () => documentsApi.getUserDocuments(userId),
  });

  // Upload document mutation
  const uploadMutation = useMutation({
    mutationFn: (data: { file: File; title: string; tags?: string }) =>
      documentsApi.uploadDocument({
        user_id: userId,
        file: data.file,
        title: data.title,
        tags: data.tags,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      setIsUploadDialogOpen(false);
      setUploadTitle("");
      setUploadTags("");
      setUploadFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    },
  });

  // Delete document mutation
  const deleteMutation = useMutation({
    mutationFn: (docId: string) =>
      documentsApi.deleteDocument({ user_id: userId, doc_id: docId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      setIsDetailDialogOpen(false);
    },
  });

  const handleUpload = () => {
    if (uploadFile && uploadTitle.trim()) {
      uploadMutation.mutate({
        file: uploadFile,
        title: uploadTitle,
        tags: uploadTags,
      });
    }
  };

  const handleDeleteDocument = () => {
    if (selectedDocument) {
      deleteMutation.mutate(selectedDocument.doc_id);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadFile(file);
      // Auto-fill title if empty
      if (!uploadTitle) {
        setUploadTitle(file.name.replace(/\.[^/.]+$/, ""));
      }
    }
  };

  // Filter documents by search query
  const filteredDocuments = searchQuery
    ? documents?.filter(
        (doc) =>
          doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          doc.path.toLowerCase().includes(searchQuery.toLowerCase()) ||
          doc.tags.some((tag) =>
            tag.toLowerCase().includes(searchQuery.toLowerCase())
          )
      )
    : documents;

  // Calculate stats
  const stats = {
    total: documents?.length || 0,
    totalChunks: documents?.reduce((sum, doc) => sum + doc.chunk_count, 0) || 0,
    totalChars: documents?.reduce((sum, doc) => sum + doc.total_chars, 0) || 0,
  };

  return (
    <div className="h-full space-y-4">
      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Documents</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Chunks</CardTitle>
            <FileCode className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalChunks}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Characters</CardTitle>
            <FileCode className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalChars.toLocaleString()}</div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Card className="flex-1">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Knowledge Base</CardTitle>
            <Button onClick={() => setIsUploadDialogOpen(true)}>
              <Upload className="mr-2 h-4 w-4" />
              Upload Document
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search Bar */}
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search documents by title, path, or tags..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
          </div>

          {/* Documents List */}
          <ScrollArea className="h-[500px]">
            {isLoading ? (
              <div className="flex items-center justify-center h-40">
                <p className="text-muted-foreground">Loading documents...</p>
              </div>
            ) : filteredDocuments && filteredDocuments.length > 0 ? (
              <div className="space-y-2">
                {filteredDocuments.map((document) => (
                  <div
                    key={document.doc_id}
                    className="flex items-start gap-4 p-4 border rounded-lg hover:bg-accent cursor-pointer transition-colors"
                    onClick={() => {
                      setSelectedDocument(document);
                      setIsDetailDialogOpen(true);
                    }}
                  >
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium">{document.title}</h3>
                        {document.tags.length > 0 && (
                          <div className="flex gap-1">
                            {document.tags.slice(0, 3).map((tag) => (
                              <Badge key={tag} variant="secondary">
                                {tag}
                              </Badge>
                            ))}
                            {document.tags.length > 3 && (
                              <Badge variant="secondary">
                                +{document.tags.length - 3}
                              </Badge>
                            )}
                          </div>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">{document.path}</p>
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {new Date(document.updated_at).toLocaleDateString()}
                        </span>
                        <span>{document.chunk_count} chunks</span>
                        <span>{document.total_chars.toLocaleString()} chars</span>
                        <Badge variant="outline">{document.source_type}</Badge>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedDocument(document);
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
                <p className="text-muted-foreground">No documents found</p>
                <p className="text-sm text-muted-foreground">
                  Try adjusting your search or upload a new document
                </p>
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Upload Dialog */}
      <Dialog open={isUploadDialogOpen} onOpenChange={setIsUploadDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Upload Document</DialogTitle>
            <DialogDescription>
              Upload a document to your knowledge base (PDF, TXT, MD)
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="file-upload">File</Label>
              <Input
                id="file-upload"
                type="file"
                accept=".pdf,.txt,.md"
                onChange={handleFileChange}
                ref={fileInputRef}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="doc-title">Title</Label>
              <Input
                id="doc-title"
                placeholder="Document title"
                value={uploadTitle}
                onChange={(e) => setUploadTitle(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="doc-tags">Tags (comma-separated)</Label>
              <Input
                id="doc-tags"
                placeholder="tag1, tag2, tag3"
                value={uploadTags}
                onChange={(e) => setUploadTags(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsUploadDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleUpload}
              disabled={!uploadFile || !uploadTitle.trim() || uploadMutation.isPending}
            >
              {uploadMutation.isPending ? "Uploading..." : "Upload"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Document Detail Dialog */}
      <Dialog open={isDetailDialogOpen} onOpenChange={setIsDetailDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Document Details</DialogTitle>
          </DialogHeader>
          {selectedDocument && (
            <div className="space-y-4">
              <div>
                <Label>Title</Label>
                <p className="text-sm mt-2 font-medium">{selectedDocument.title}</p>
              </div>
              <div>
                <Label>Path</Label>
                <p className="text-sm mt-2 text-muted-foreground">{selectedDocument.path}</p>
              </div>
              <div>
                <Label>Tags</Label>
                <div className="flex gap-1 mt-2 flex-wrap">
                  {selectedDocument.tags.length > 0 ? (
                    selectedDocument.tags.map((tag) => (
                      <Badge key={tag} variant="secondary">
                        {tag}
                      </Badge>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">No tags</p>
                  )}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <Label>Created</Label>
                  <p className="text-muted-foreground mt-1">
                    {new Date(selectedDocument.created_at).toLocaleString()}
                  </p>
                </div>
                <div>
                  <Label>Updated</Label>
                  <p className="text-muted-foreground mt-1">
                    {new Date(selectedDocument.updated_at).toLocaleString()}
                  </p>
                </div>
                <div>
                  <Label>Chunks</Label>
                  <p className="text-muted-foreground mt-1">
                    {selectedDocument.chunk_count}
                  </p>
                </div>
                <div>
                  <Label>Characters</Label>
                  <p className="text-muted-foreground mt-1">
                    {selectedDocument.total_chars.toLocaleString()}
                  </p>
                </div>
                <div className="col-span-2">
                  <Label>Source Type</Label>
                  <p className="text-muted-foreground mt-1">{selectedDocument.source_type}</p>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button
              variant="destructive"
              onClick={handleDeleteDocument}
              disabled={deleteMutation.isPending}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              {deleteMutation.isPending ? "Deleting..." : "Delete"}
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
