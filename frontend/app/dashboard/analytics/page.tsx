"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface Overview {
  total_requests: number;
  avg_latency_ms: number;
  error_rate: number;
}

interface RequestsOverTimeEntry {
  date: string;
  request_count: number;
}

interface TopRoute {
  route_id: string;
  slug: string;
  request_count: number;
}

interface RejectionEntry {
  reason: string;
  count: number;
}

export default function AnalyticsPage() {
  const { data: overview } = useQuery<Overview>({
    queryKey: ["analytics", "overview"],
    queryFn: async () => (await api.get("/v1/analytics/overview")).data,
  });

  const { data: timeSeries } = useQuery<RequestsOverTimeEntry[]>({
    queryKey: ["analytics", "requests-over-time"],
    queryFn: async () => (await api.get("/v1/analytics/requests-over-time")).data,
  });

  const { data: topRoutes } = useQuery<TopRoute[]>({
    queryKey: ["analytics", "top-routes"],
    queryFn: async () => (await api.get("/v1/analytics/top-routes")).data,
  });

  const { data: rejections } = useQuery<RejectionEntry[]>({
    queryKey: ["analytics", "rejections"],
    queryFn: async () => (await api.get("/v1/analytics/rejections")).data,
  });

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">Analytics</h1>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label="Total Requests" value={overview?.total_requests ?? 0} />
        <StatCard label="Avg Latency" value={`${overview?.avg_latency_ms ?? 0} ms`} />
        <StatCard label="Error Rate" value={`${overview?.error_rate ?? 0}%`} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium text-slate-500 dark:text-slate-400">
            Requests over time (30 days)
          </CardTitle>
        </CardHeader>
        <CardContent className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={timeSeries ?? []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#64748b" />
              <YAxis tick={{ fontSize: 12 }} stroke="#64748b" />
              <Tooltip />
              <Line type="monotone" dataKey="request_count" stroke="#4f46e5" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium text-slate-500 dark:text-slate-400">Top routes</CardTitle>
        </CardHeader>
        <CardContent className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={topRoutes ?? []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="slug" tick={{ fontSize: 12 }} stroke="#64748b" />
              <YAxis tick={{ fontSize: 12 }} stroke="#64748b" />
              <Tooltip />
              <Bar dataKey="request_count" fill="#4f46e5" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium text-slate-500 dark:text-slate-400">
            Rejected requests by reason
          </CardTitle>
        </CardHeader>
        <CardContent>
          {rejections && rejections.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Reason</TableHead>
                  <TableHead className="text-right">Count</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rejections.map((r) => (
                  <TableRow key={r.reason}>
                    <TableCell className="capitalize">{r.reason.replace(/_/g, " ")}</TableCell>
                    <TableCell className="text-right font-medium text-red-600 dark:text-red-400">
                      {r.count}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="text-sm text-slate-500 dark:text-slate-400">No rejected requests yet.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium text-slate-500 dark:text-slate-400">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-semibold text-indigo-600 dark:text-indigo-400">{value}</p>
      </CardContent>
    </Card>
  );
}
