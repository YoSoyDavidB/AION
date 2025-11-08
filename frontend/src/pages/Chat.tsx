import { useState, useRef, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { chatApi } from "@/lib/api/chat";
import { documentsApi } from "@/lib/api/documents";
import type { ChatMessage, ChatRequest } from "@/lib/types/chat";
import {
  Send,
  Loader2,
  Upload,
  X,
  Calculator,
  Search,
  Code,
  Database,
  Bot,
  User,
} from "lucide-react";

const AVAILABLE_TOOLS = [
  { id: "calculator", name: "Calculator", icon: Calculator },
  { id: "web_search", name: "Web Search", icon: Search },
  { id: "code_executor", name: "Code Executor", icon: Code },
  { id: "knowledge_base_search", name: "Knowledge Base", icon: Database },
];

export function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [enabledTools, setEnabledTools] = useState({
    calculator: true,
    web_search: true,
    code_executor: true,
    knowledge_base_search: true,
  });
  const [useMemory, setUseMemory] = useState(true);
  const [useKnowledgeBase, setUseKnowledgeBase] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const uploadFileMutation = useMutation({
    mutationFn: async (file: File) => {
      return documentsApi.uploadDocument({
        user_id: import.meta.env.VITE_DEFAULT_USER_ID || "david",
        title: file.name,
        file: file,
      });
    },
  });

  const chatMutation = useMutation({
    mutationFn: async (request: ChatRequest) => {
      return chatApi.sendMessage(request);
    },
    onSuccess: (data) => {
      // Add assistant response to messages
      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: data.message,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setConversationId(data.conversation_id);
    },
  });

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() && !selectedFile) return;

    // Upload file if selected
    if (selectedFile) {
      try {
        await uploadFileMutation.mutateAsync(selectedFile);
        handleRemoveFile();
      } catch (error) {
        console.error("Error uploading file:", error);
        return;
      }
    }

    // Add user message
    const userMessage: ChatMessage = {
      role: "user",
      content: input,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Prepare chat request
    const request: ChatRequest = {
      user_id: import.meta.env.VITE_DEFAULT_USER_ID || "david",
      message: input,
      conversation_id: conversationId,
      use_memory: useMemory,
      use_knowledge_base: useKnowledgeBase,
      use_tools: Object.values(enabledTools).some((v) => v),
    };

    // Clear input
    setInput("");

    // Send message
    chatMutation.mutate(request);
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleTool = (toolId: keyof typeof enabledTools) => {
    setEnabledTools((prev) => ({
      ...prev,
      [toolId]: !prev[toolId],
    }));
  };

  return (
    <div className="h-full flex gap-4">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        <Card className="flex-1 flex flex-col">
          <CardHeader className="border-b">
            <CardTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5" />
              Chat with AION
            </CardTitle>
          </CardHeader>

          <CardContent className="flex-1 flex flex-col p-0">
            {/* Messages Area */}
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4">
                {messages.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-center py-12">
                    <Bot className="h-12 w-12 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-semibold mb-2">
                      Start a conversation
                    </h3>
                    <p className="text-sm text-muted-foreground max-w-md">
                      Ask me anything! I can help you with calculations, web
                      searches, code execution, and knowledge base queries.
                    </p>
                  </div>
                ) : (
                  messages.map((message, index) => (
                    <div
                      key={index}
                      className={`flex gap-3 ${
                        message.role === "user" ? "justify-end" : ""
                      }`}
                    >
                      {message.role === "assistant" && (
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                          <Bot className="h-5 w-5" />
                        </div>
                      )}
                      <div
                        className={`max-w-[80%] rounded-lg px-4 py-2 ${
                          message.role === "user"
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted"
                        }`}
                      >
                        <p className="text-sm whitespace-pre-wrap">
                          {message.content}
                        </p>
                        {message.timestamp && (
                          <p
                            className={`text-xs mt-1 ${
                              message.role === "user"
                                ? "text-primary-foreground/70"
                                : "text-muted-foreground"
                            }`}
                          >
                            {new Date(message.timestamp).toLocaleTimeString()}
                          </p>
                        )}
                      </div>
                      {message.role === "user" && (
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary text-secondary-foreground">
                          <User className="h-5 w-5" />
                        </div>
                      )}
                    </div>
                  ))
                )}
                {chatMutation.isPending && (
                  <div className="flex gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                      <Bot className="h-5 w-5" />
                    </div>
                    <div className="bg-muted rounded-lg px-4 py-2">
                      <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            {/* Input Area */}
            <div className="border-t p-4 space-y-3">
              {/* File Upload Preview */}
              {selectedFile && (
                <div className="flex items-center gap-2 p-2 bg-muted rounded-lg">
                  <Upload className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm flex-1 truncate">
                    {selectedFile.name}
                  </span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={handleRemoveFile}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              )}

              <div className="flex gap-2">
                <Input
                  ref={fileInputRef}
                  type="file"
                  className="hidden"
                  onChange={handleFileSelect}
                  accept=".txt,.pdf,.doc,.docx,.md"
                />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={chatMutation.isPending}
                >
                  <Upload className="h-4 w-4" />
                </Button>
                <Textarea
                  placeholder="Type your message... (Shift+Enter for new line)"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyPress}
                  disabled={chatMutation.isPending}
                  className="min-h-[60px] max-h-[200px] resize-none"
                />
                <Button
                  onClick={handleSendMessage}
                  disabled={
                    (!input.trim() && !selectedFile) || chatMutation.isPending
                  }
                  size="icon"
                  className="h-[60px] w-12"
                >
                  {chatMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Settings Sidebar */}
      <Card className="w-80 flex flex-col">
        <CardHeader>
          <CardTitle className="text-base">Chat Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Tools Section */}
          <div className="space-y-3">
            <Label className="text-sm font-semibold">Available Tools</Label>
            <div className="space-y-2">
              {AVAILABLE_TOOLS.map((tool) => (
                <div key={tool.id} className="flex items-center space-x-2">
                  <Checkbox
                    id={tool.id}
                    checked={enabledTools[tool.id as keyof typeof enabledTools]}
                    onCheckedChange={() =>
                      toggleTool(tool.id as keyof typeof enabledTools)
                    }
                  />
                  <Label
                    htmlFor={tool.id}
                    className="text-sm font-normal cursor-pointer flex items-center gap-2"
                  >
                    <tool.icon className="h-4 w-4 text-muted-foreground" />
                    {tool.name}
                  </Label>
                </div>
              ))}
            </div>
          </div>

          {/* Context Settings */}
          <div className="space-y-3">
            <Label className="text-sm font-semibold">Context Settings</Label>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="use-memory"
                  checked={useMemory}
                  onCheckedChange={(checked) =>
                    setUseMemory(checked as boolean)
                  }
                />
                <Label
                  htmlFor="use-memory"
                  className="text-sm font-normal cursor-pointer"
                >
                  Use Long-term Memory
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="use-kb"
                  checked={useKnowledgeBase}
                  onCheckedChange={(checked) =>
                    setUseKnowledgeBase(checked as boolean)
                  }
                />
                <Label
                  htmlFor="use-kb"
                  className="text-sm font-normal cursor-pointer"
                >
                  Use Knowledge Base
                </Label>
              </div>
            </div>
          </div>

          {/* Conversation Info */}
          {conversationId && (
            <div className="space-y-2 pt-4 border-t">
              <Label className="text-sm font-semibold">
                Conversation Info
              </Label>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">
                  ID: {conversationId.substring(0, 8)}...
                </p>
                <p className="text-xs text-muted-foreground">
                  Messages: {messages.length}
                </p>
              </div>
            </div>
          )}

          {/* File Upload Info */}
          <div className="space-y-2 pt-4 border-t">
            <Label className="text-sm font-semibold">File Upload</Label>
            <p className="text-xs text-muted-foreground">
              Upload documents to add them to your knowledge base. Supported
              formats: TXT, PDF, DOC, DOCX, MD
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
