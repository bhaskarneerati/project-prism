"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Check, Copy, ArrowUpDown } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface ApiKey {
  id: string;
  name: string;
  is_active: boolean;
  expires_at: string | null;
  created_at: string;
}

export default function ApiKeysPage() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [expiresAt, setExpiresAt] = useState("");
  const [rawKey, setRawKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [revokeTarget, setRevokeTarget] = useState<ApiKey | null>(null);
  const [sortAsc, setSortAsc] = useState(false);

  const { data: keys, isLoading } = useQuery<ApiKey[]>({
    queryKey: ["api-keys"],
    queryFn: async () => (await api.get("/v1/api-keys")).data,
  });

  const createMutation = useMutation({
    mutationFn: async () =>
      (
        await api.post("/v1/api-keys", {
          name,
          expires_at: expiresAt ? new Date(expiresAt).toISOString() : null,
        })
      ).data,
    onSuccess: (data) => {
      setRawKey(data.raw_key);
      setName("");
      setExpiresAt("");
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
      toast.success("API key created");
    },
    onError: () => toast.error("Failed to create API key"),
  });

  const revokeMutation = useMutation({
    mutationFn: async (id: string) => api.delete(`/v1/api-keys/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
      toast.success("API key revoked");
    },
    onError: () => toast.error("Failed to revoke API key"),
  });

  function handleDialogClose(isOpen: boolean) {
    setOpen(isOpen);
    if (!isOpen) {
      setRawKey(null);
      setCopied(false);
    }
  }

  function handleCopy() {
    if (!rawKey) return;
    navigator.clipboard.writeText(rawKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const todayStr = new Date().toISOString().split("T")[0];
  const expiryIsPast = expiresAt !== "" && expiresAt < todayStr;

  const sortedKeys = keys
    ? [...keys].sort((a, b) => {
        const diff = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        return sortAsc ? diff : -diff;
      })
    : [];

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">API Keys</h1>
        <Dialog open={open} onOpenChange={handleDialogClose}>
          <DialogTrigger asChild>
            <Button>Create Key</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{rawKey ? "Key created" : "Create API key"}</DialogTitle>
            </DialogHeader>
            {rawKey ? (
              <div className="flex flex-col gap-2">
                <p className="text-sm text-slate-500">
                  Copy this key now — it will not be shown again.
                </p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 break-all rounded-md bg-slate-100 p-3 text-sm">
                    {rawKey}
                  </code>
                  <Button variant="outline" size="icon" onClick={handleCopy}>
                    {copied ? <Check className="size-4" /> : <Copy className="size-4" />}
                  </Button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col gap-4">
                <div className="flex flex-col gap-2">
                  <Label htmlFor="key-name">Name</Label>
                  <Input id="key-name" value={name} onChange={(e) => setName(e.target.value)} />
                </div>
                <div className="flex flex-col gap-2">
                  <Label htmlFor="key-expiry">Expires at (optional)</Label>
                  <Input
                    id="key-expiry"
                    type="date"
                    min={todayStr}
                    value={expiresAt}
                    onChange={(e) => setExpiresAt(e.target.value)}
                  />
                  {expiryIsPast && (
                    <p className="text-sm text-red-600">Expiry date can&apos;t be in the past.</p>
                  )}
                </div>
              </div>
            )}
            <DialogFooter>
              {rawKey ? (
                <Button onClick={() => handleDialogClose(false)}>Done</Button>
              ) : (
                <Button
                  disabled={!name || expiryIsPast || createMutation.isPending}
                  onClick={() => createMutation.mutate()}
                >
                  Create
                </Button>
              )}
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {isLoading ? (
        <div className="flex flex-col gap-2">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      ) : sortedKeys.length === 0 ? (
        <p className="text-sm text-slate-500">No API keys yet — create one to get started.</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>
                <button
                  className="flex items-center gap-1"
                  onClick={() => setSortAsc((prev) => !prev)}
                >
                  Created At <ArrowUpDown className="size-3" />
                </button>
              </TableHead>
              <TableHead>Expires At</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedKeys.map((key) => (
              <TableRow key={key.id}>
                <TableCell>{key.name}</TableCell>
                <TableCell>{new Date(key.created_at).toLocaleString()}</TableCell>
                <TableCell>
                  {key.expires_at ? new Date(key.expires_at).toLocaleDateString() : "—"}
                </TableCell>
                <TableCell>
                  <Badge variant={key.is_active ? "default" : "secondary"}>
                    {key.is_active ? "Active" : "Revoked"}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!key.is_active}
                    onClick={() => setRevokeTarget(key)}
                  >
                    Revoke
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <AlertDialog open={!!revokeTarget} onOpenChange={(open) => !open && setRevokeTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Revoke API key?</AlertDialogTitle>
            <AlertDialogDescription>
              This will immediately deactivate &quot;{revokeTarget?.name}&quot;. Any requests
              using this key will be rejected.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (revokeTarget) revokeMutation.mutate(revokeTarget.id);
                setRevokeTarget(null);
              }}
            >
              Revoke
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
