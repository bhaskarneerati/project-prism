"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ArrowUpDown } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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

interface Route {
  id: string;
  slug: string;
  target_url: string;
  created_at: string;
}

export default function RoutesPage() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [slug, setSlug] = useState("");
  const [targetUrl, setTargetUrl] = useState("");
  const [error, setError] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Route | null>(null);
  const [sortAsc, setSortAsc] = useState(false);

  const { data: routes, isLoading } = useQuery<Route[]>({
    queryKey: ["routes"],
    queryFn: async () => (await api.get("/v1/routes")).data,
  });

  const createMutation = useMutation({
    mutationFn: async () =>
      (await api.post("/v1/routes", { slug, target_url: targetUrl })).data,
    onSuccess: () => {
      setSlug("");
      setTargetUrl("");
      setError("");
      setOpen(false);
      queryClient.invalidateQueries({ queryKey: ["routes"] });
      toast.success("Route created");
    },
    onError: (err: unknown) => {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Failed to create route";
      setError(message);
      toast.error(message);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => api.delete(`/v1/routes/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["routes"] });
      toast.success("Route deleted");
    },
    onError: () => toast.error("Failed to delete route"),
  });

  const sortedRoutes = routes
    ? [...routes].sort((a, b) => {
        const diff = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        return sortAsc ? diff : -diff;
      })
    : [];

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">Routes</h1>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>Add Route</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Register a proxy route</DialogTitle>
            </DialogHeader>
            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-2">
                <Label htmlFor="slug">Slug</Label>
                <Input id="slug" value={slug} onChange={(e) => setSlug(e.target.value)} />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="target_url">Target URL</Label>
                <Input
                  id="target_url"
                  value={targetUrl}
                  onChange={(e) => setTargetUrl(e.target.value)}
                />
              </div>
              {error && <p className="text-sm text-red-600">{error}</p>}
            </div>
            <DialogFooter>
              <Button
                disabled={!slug || !targetUrl || createMutation.isPending}
                onClick={() => createMutation.mutate()}
              >
                Create
              </Button>
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
      ) : sortedRoutes.length === 0 ? (
        <p className="text-sm text-slate-500">No routes yet — add one to get started.</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Slug</TableHead>
              <TableHead>Target URL</TableHead>
              <TableHead>
                <button
                  className="flex items-center gap-1"
                  onClick={() => setSortAsc((prev) => !prev)}
                >
                  Created At <ArrowUpDown className="size-3" />
                </button>
              </TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedRoutes.map((route) => (
              <TableRow key={route.id}>
                <TableCell>{route.slug}</TableCell>
                <TableCell className="max-w-xs truncate">{route.target_url}</TableCell>
                <TableCell>{new Date(route.created_at).toLocaleString()}</TableCell>
                <TableCell>
                  <Button variant="outline" size="sm" onClick={() => setDeleteTarget(route)}>
                    Delete
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <AlertDialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete route?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete &quot;{deleteTarget?.slug}&quot;. Any proxy calls to
              this route will start returning 404.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (deleteTarget) deleteMutation.mutate(deleteTarget.id);
                setDeleteTarget(null);
              }}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
