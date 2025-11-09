import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Github,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  Database,
  Mail,
  Calendar,
} from "lucide-react";
import { obsidianApi } from "@/lib/api/obsidian";
import { integrationsApi } from "@/lib/api/integrations";

export function Settings() {
  const [lastSyncResult, setLastSyncResult] = useState<any>(null);
  const queryClient = useQueryClient();
  const userId = import.meta.env.VITE_DEFAULT_USER_ID || "david";

  // Check for OAuth callback success
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("google_connected") === "true") {
      queryClient.invalidateQueries({ queryKey: ["google-status"] });
    }
    if (params.get("microsoft_connected") === "true") {
      queryClient.invalidateQueries({ queryKey: ["microsoft-status"] });
    }
  }, [queryClient]);

  // Google integration status
  const { data: googleStatus, isLoading: googleStatusLoading } = useQuery({
    queryKey: ["google-status", userId],
    queryFn: () => integrationsApi.google.getStatus(userId),
    refetchInterval: 30000,
  });

  // Microsoft integration status
  const { data: microsoftStatus, isLoading: microsoftStatusLoading } = useQuery({
    queryKey: ["microsoft-status", userId],
    queryFn: () => integrationsApi.microsoft.getStatus(userId),
    refetchInterval: 30000,
  });

  // Google disconnect mutation
  const googleDisconnectMutation = useMutation({
    mutationFn: () => integrationsApi.google.disconnect(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["google-status"] });
    },
  });

  // Microsoft disconnect mutation
  const microsoftDisconnectMutation = useMutation({
    mutationFn: () => integrationsApi.microsoft.disconnect(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["microsoft-status"] });
    },
  });

  // Get sync status
  const { data: syncStatus, isLoading: statusLoading } = useQuery({
    queryKey: ["obsidian-sync-status", userId],
    queryFn: () => obsidianApi.getSyncStatus(userId),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Sync mutation
  const syncMutation = useMutation({
    mutationFn: (force: boolean = false) =>
      obsidianApi.syncVault({ user_id: userId, force }),
    onSuccess: (data) => {
      setLastSyncResult(data);
      queryClient.invalidateQueries({ queryKey: ["obsidian-sync-status"] });
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  // Cleanup mutation
  const cleanupMutation = useMutation({
    mutationFn: () => obsidianApi.cleanup(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["obsidian-sync-status"] });
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  const handleSync = (force: boolean = false) => {
    setLastSyncResult(null);
    syncMutation.mutate(force);
  };

  const handleCleanup = () => {
    cleanupMutation.mutate();
  };

  return (
    <div className="h-full space-y-6 p-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
        <p className="text-muted-foreground">
          Manage your AION configuration and synchronization
        </p>
      </div>

      {/* Obsidian Sync Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Github className="h-5 w-5" />
            <CardTitle>Obsidian Vault Sync</CardTitle>
          </div>
          <CardDescription>
            Synchronize your Obsidian vault from GitHub to AION's knowledge base
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Configuration Status */}
          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-medium mb-3">Configuration Status</h4>
              {statusLoading ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Loading configuration...</span>
                </div>
              ) : syncStatus?.vault_configured ? (
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                    <span className="text-sm font-medium">Connected to GitHub</span>
                  </div>
                  <div className="ml-6 space-y-1 text-sm text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <Database className="h-3 w-3" />
                      <span>Repository: {syncStatus.vault_path}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-3 w-3" />
                      <span>Synced files: {syncStatus.total_synced_files}</span>
                    </div>
                  </div>
                </div>
              ) : (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    GitHub repository not configured. Please set GITHUB_TOKEN,
                    GITHUB_REPO_OWNER, and GITHUB_REPO_NAME in your .env file.
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </div>

          {/* Sync Actions */}
          {syncStatus?.vault_configured && (
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium mb-3">Actions</h4>
                <div className="flex flex-wrap gap-3">
                  <Button
                    onClick={() => handleSync(false)}
                    disabled={syncMutation.isPending}
                  >
                    {syncMutation.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Syncing...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="mr-2 h-4 w-4" />
                        Sync Now
                      </>
                    )}
                  </Button>

                  <Button
                    variant="outline"
                    onClick={() => handleSync(true)}
                    disabled={syncMutation.isPending}
                  >
                    Force Sync All
                  </Button>

                  <Button
                    variant="outline"
                    onClick={handleCleanup}
                    disabled={cleanupMutation.isPending}
                  >
                    {cleanupMutation.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Cleaning...
                      </>
                    ) : (
                      "Cleanup Deleted"
                    )}
                  </Button>
                </div>
              </div>

              {/* Last Sync Result */}
              {lastSyncResult && (
                <div>
                  <h4 className="text-sm font-medium mb-3">Last Sync Result</h4>
                  <div className="border rounded-lg p-4 space-y-3">
                    <div className="flex items-start gap-3">
                      {lastSyncResult.failed > 0 ? (
                        <XCircle className="h-5 w-5 text-red-600 mt-0.5" />
                      ) : (
                        <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
                      )}
                      <div className="flex-1 space-y-2">
                        <p className="text-sm font-medium">
                          {lastSyncResult.failed > 0
                            ? "Sync completed with errors"
                            : "Sync completed successfully"}
                        </p>
                        <div className="grid grid-cols-2 gap-3 text-sm">
                          <div className="flex items-center justify-between">
                            <span className="text-muted-foreground">Total files:</span>
                            <Badge variant="secondary">
                              {lastSyncResult.total_files}
                            </Badge>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-muted-foreground">Synced:</span>
                            <Badge
                              variant={lastSyncResult.synced > 0 ? "default" : "secondary"}
                            >
                              {lastSyncResult.synced}
                            </Badge>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-muted-foreground">Skipped:</span>
                            <Badge variant="secondary">{lastSyncResult.skipped}</Badge>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-muted-foreground">Failed:</span>
                            <Badge
                              variant={lastSyncResult.failed > 0 ? "destructive" : "secondary"}
                            >
                              {lastSyncResult.failed}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Cleanup Result */}
              {cleanupMutation.isSuccess && cleanupMutation.data && (
                <Alert>
                  <CheckCircle2 className="h-4 w-4" />
                  <AlertDescription>
                    Cleaned up {cleanupMutation.data.cleaned_files} deleted file(s)
                  </AlertDescription>
                </Alert>
              )}

              {/* Error Messages */}
              {syncMutation.isError && (
                <Alert variant="destructive">
                  <XCircle className="h-4 w-4" />
                  <AlertDescription>
                    Sync failed: {(syncMutation.error as Error).message}
                  </AlertDescription>
                </Alert>
              )}

              {cleanupMutation.isError && (
                <Alert variant="destructive">
                  <XCircle className="h-4 w-4" />
                  <AlertDescription>
                    Cleanup failed: {(cleanupMutation.error as Error).message}
                  </AlertDescription>
                </Alert>
              )}
            </div>
          )}

          {/* Help Text */}
          <div className="border-t pt-4">
            <h4 className="text-sm font-medium mb-2">How it works</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="flex items-start gap-2">
                <span className="mt-1">•</span>
                <span>
                  AION syncs markdown files directly from your GitHub repository
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1">•</span>
                <span>
                  Only new and modified files are synced (incremental sync)
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1">•</span>
                <span>
                  Files in .obsidian, .git, .trash, and templates folders are excluded
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1">•</span>
                <span>
                  Force Sync All will re-sync all files regardless of their state
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1">•</span>
                <span>
                  Cleanup Deleted removes documents for files that no longer exist in
                  the repository
                </span>
              </li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Google Integration Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Mail className="h-5 w-5" />
            <CardTitle>Google Integration</CardTitle>
          </div>
          <CardDescription>
            Connect your Google account to access Calendar and Gmail
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Google Status */}
          <div>
            <h4 className="text-sm font-medium mb-3">Connection Status</h4>
            {googleStatusLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Loading status...</span>
              </div>
            ) : googleStatus?.is_connected ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <span className="text-sm font-medium">Connected to Google</span>
                </div>
                <div className="ml-6 space-y-1 text-sm text-muted-foreground">
                  {googleStatus.user_email && (
                    <div className="flex items-center gap-2">
                      <Mail className="h-3 w-3" />
                      <span>{googleStatus.user_email}</span>
                    </div>
                  )}
                  {googleStatus.user_name && (
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-3 w-3" />
                      <span>{googleStatus.user_name}</span>
                    </div>
                  )}
                  {googleStatus.connected_at && (
                    <div className="text-xs">
                      Connected: {new Date(googleStatus.connected_at).toLocaleDateString()}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Not connected to Google. Click "Connect" to authorize access to your
                  Calendar and Gmail.
                </AlertDescription>
              </Alert>
            )}
          </div>

          {/* Google Actions */}
          <div>
            <h4 className="text-sm font-medium mb-3">Actions</h4>
            <div className="flex flex-wrap gap-3">
              {googleStatus?.is_connected ? (
                <Button
                  variant="destructive"
                  onClick={() => googleDisconnectMutation.mutate()}
                  disabled={googleDisconnectMutation.isPending}
                >
                  {googleDisconnectMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Disconnecting...
                    </>
                  ) : (
                    "Disconnect Google"
                  )}
                </Button>
              ) : (
                <Button
                  onClick={() => integrationsApi.google.authorize(userId)}
                >
                  <Mail className="mr-2 h-4 w-4" />
                  Connect Google
                </Button>
              )}
            </div>
          </div>

          {/* Error Messages */}
          {googleDisconnectMutation.isError && (
            <Alert variant="destructive">
              <XCircle className="h-4 w-4" />
              <AlertDescription>
                Disconnect failed: {(googleDisconnectMutation.error as Error).message}
              </AlertDescription>
            </Alert>
          )}

          {/* Help Text */}
          <div className="border-t pt-4">
            <h4 className="text-sm font-medium mb-2">Available Features</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="flex items-start gap-2">
                <span className="mt-1">•</span>
                <span>Access your Google Calendar events</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1">•</span>
                <span>Read your Gmail messages</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1">•</span>
                <span>AION can use this data to provide contextual assistance</span>
              </li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Microsoft Integration Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            <CardTitle>Microsoft Integration</CardTitle>
          </div>
          <CardDescription>
            Connect your Microsoft account to access Outlook Calendar and Email
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Microsoft Status */}
          <div>
            <h4 className="text-sm font-medium mb-3">Connection Status</h4>
            {microsoftStatusLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Loading status...</span>
              </div>
            ) : microsoftStatus?.is_connected ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <span className="text-sm font-medium">Connected to Microsoft</span>
                </div>
                <div className="ml-6 space-y-1 text-sm text-muted-foreground">
                  {microsoftStatus.user_email && (
                    <div className="flex items-center gap-2">
                      <Mail className="h-3 w-3" />
                      <span>{microsoftStatus.user_email}</span>
                    </div>
                  )}
                  {microsoftStatus.user_name && (
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-3 w-3" />
                      <span>{microsoftStatus.user_name}</span>
                    </div>
                  )}
                  {microsoftStatus.connected_at && (
                    <div className="text-xs">
                      Connected: {new Date(microsoftStatus.connected_at).toLocaleDateString()}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Not connected to Microsoft. Click "Connect" to authorize access to your
                  Outlook Calendar and Email.
                </AlertDescription>
              </Alert>
            )}
          </div>

          {/* Microsoft Actions */}
          <div>
            <h4 className="text-sm font-medium mb-3">Actions</h4>
            <div className="flex flex-wrap gap-3">
              {microsoftStatus?.is_connected ? (
                <Button
                  variant="destructive"
                  onClick={() => microsoftDisconnectMutation.mutate()}
                  disabled={microsoftDisconnectMutation.isPending}
                >
                  {microsoftDisconnectMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Disconnecting...
                    </>
                  ) : (
                    "Disconnect Microsoft"
                  )}
                </Button>
              ) : (
                <Button
                  onClick={() => integrationsApi.microsoft.authorize(userId)}
                >
                  <Calendar className="mr-2 h-4 w-4" />
                  Connect Microsoft
                </Button>
              )}
            </div>
          </div>

          {/* Error Messages */}
          {microsoftDisconnectMutation.isError && (
            <Alert variant="destructive">
              <XCircle className="h-4 w-4" />
              <AlertDescription>
                Disconnect failed: {(microsoftDisconnectMutation.error as Error).message}
              </AlertDescription>
            </Alert>
          )}

          {/* Help Text */}
          <div className="border-t pt-4">
            <h4 className="text-sm font-medium mb-2">Available Features</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="flex items-start gap-2">
                <span className="mt-1">•</span>
                <span>Access your Outlook Calendar events</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1">•</span>
                <span>Read your Outlook Email messages</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1">•</span>
                <span>AION can use this data to provide contextual assistance</span>
              </li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Future Settings Sections */}
      <Card>
        <CardHeader>
          <CardTitle>General Settings</CardTitle>
          <CardDescription>
            Application preferences and configuration
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Additional settings coming soon...
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
