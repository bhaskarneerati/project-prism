"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface Overview {
  total_requests: number;
  avg_latency_ms: number;
  error_rate: number;
}

export default function OverviewPage() {
  const { data, isLoading, isError } = useQuery<Overview>({
    queryKey: ["analytics", "overview"],
    queryFn: async () => (await api.get("/v1/analytics/overview")).data,
  });

  if (isError) return <p className="text-red-600">Failed to load overview.</p>;

  return (
    <div>
      <h1 className="mb-6 text-2xl font-semibold text-slate-900 dark:text-slate-50">Overview</h1>
      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatCard label="Total Requests" value={data?.total_requests ?? 0} />
          <StatCard label="Avg Latency" value={`${data?.avg_latency_ms ?? 0} ms`} />
          <StatCard label="Error Rate" value={`${data?.error_rate ?? 0}%`} />
        </div>
      )}
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
