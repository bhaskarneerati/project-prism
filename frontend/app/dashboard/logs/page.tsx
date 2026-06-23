"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface LogEntry {
  id: string;
  route_id: string;
  api_key_id: string;
  timestamp: string;
  latency_ms: number;
  status_code: number;
  request_method: string;
}

interface PaginatedLogs {
  page: number;
  page_size: number;
  total: number;
  logs: LogEntry[];
}

interface Route {
  id: string;
  slug: string;
}

function statusBadgeClassName(statusCode: number): string {
  if (statusCode < 300) return "bg-green-100 text-green-700 hover:bg-green-100";
  if (statusCode === 429) return "bg-amber-100 text-amber-700 hover:bg-amber-100";
  return "bg-red-100 text-red-700 hover:bg-red-100";
}

const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

export default function LogsPage() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [routeId, setRouteId] = useState<string>("all");
  const [statusCode, setStatusCode] = useState<string>("all");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");

  const { data: routes } = useQuery<Route[]>({
    queryKey: ["routes"],
    queryFn: async () => (await api.get("/v1/routes")).data,
  });

  const { data, isLoading } = useQuery<PaginatedLogs>({
    queryKey: ["analytics", "logs", page, pageSize, routeId, statusCode, fromDate, toDate],
    queryFn: async () => {
      const params: Record<string, string | number> = { page, page_size: pageSize };
      if (routeId !== "all") params.route_id = routeId;
      if (statusCode !== "all") params.status_code = statusCode;
      if (fromDate) params.from_date = new Date(fromDate).toISOString();
      if (toDate) params.to_date = new Date(toDate).toISOString();
      return (await api.get("/v1/analytics/logs", { params })).data;
    },
  });

  const totalPages = data ? Math.max(1, Math.ceil(data.total / pageSize)) : 1;

  return (
    <div>
      <h1 className="mb-6 text-2xl font-semibold text-slate-900 dark:text-slate-50">Logs</h1>

      <div className="mb-4 flex flex-wrap items-end gap-3">
        <Select
          value={routeId}
          onValueChange={(value) => {
            setRouteId(value);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Filter by route" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All routes</SelectItem>
            {routes?.map((route) => (
              <SelectItem key={route.id} value={route.id}>
                {route.slug}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={statusCode}
          onValueChange={(value) => {
            setStatusCode(value);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="200">200</SelectItem>
            <SelectItem value="404">404</SelectItem>
            <SelectItem value="429">429</SelectItem>
            <SelectItem value="500">500</SelectItem>
          </SelectContent>
        </Select>

        <div className="flex flex-col gap-1">
          <Label htmlFor="from-date" className="text-xs text-slate-500">
            From
          </Label>
          <Input
            id="from-date"
            type="date"
            className="w-40"
            value={fromDate}
            onChange={(e) => {
              setFromDate(e.target.value);
              setPage(1);
            }}
          />
        </div>

        <div className="flex flex-col gap-1">
          <Label htmlFor="to-date" className="text-xs text-slate-500">
            To
          </Label>
          <Input
            id="to-date"
            type="date"
            className="w-40"
            value={toDate}
            onChange={(e) => {
              setToDate(e.target.value);
              setPage(1);
            }}
          />
        </div>

        <Select
          value={String(pageSize)}
          onValueChange={(value) => {
            setPageSize(Number(value));
            setPage(1);
          }}
        >
          <SelectTrigger className="w-32">
            <SelectValue placeholder="Page size" />
          </SelectTrigger>
          <SelectContent>
            {PAGE_SIZE_OPTIONS.map((size) => (
              <SelectItem key={size} value={String(size)}>
                {size} / page
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <div className="flex flex-col gap-2">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      ) : data?.logs.length === 0 ? (
        <p className="text-sm text-slate-500">No logs match the current filters.</p>
      ) : (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>Method</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Latency</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.logs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell>{new Date(log.timestamp).toLocaleString()}</TableCell>
                  <TableCell>{log.request_method}</TableCell>
                  <TableCell>
                    <Badge className={statusBadgeClassName(log.status_code)}>
                      {log.status_code}
                    </Badge>
                  </TableCell>
                  <TableCell>{log.latency_ms} ms</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          <div className="mt-4 flex items-center justify-between">
            <p className="text-sm text-slate-500">
              Page {page} of {totalPages} ({data?.total ?? 0} total)
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
