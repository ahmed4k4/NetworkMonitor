"use client";

import { useCallback, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { DataTable } from "@/components/design-system";
import { StatusBadge } from "@/components/design-system";
import { api, isAuthenticated } from "@/lib/api";
import { Flow } from "@/lib/types";
import { ArrowUp, ArrowDown, RefreshCw, Clock, Wifi, WifiOff } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";

export default function FlowsPage() {
  const router = useRouter();
  const [flows, setFlows] = useState<Flow[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("all");
  const [error, setError] = useState<string | null>(null);

  const loadFlowsData = useCallback(async () => {
    try {
      const flowsResult = await api.getFlows();
      setFlows(Array.isArray(flowsResult) ? flowsResult : []);
    } catch (err) {
      console.error("Failed to load flows data:", err);
      setError(err instanceof Error ? err.message : "Failed to load flows data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }

    const timer = setTimeout(() => {
      loadFlowsData();
    }, 0);

    return () => clearTimeout(timer);
  }, [router, loadFlowsData]);

  const filteredFlows = flows.filter((flow) => {
    if (statusFilter !== "all") {
      const isActive = flow.state === "ACTIVE";
      if (statusFilter === "active" && !isActive) return false;
      if (statusFilter === "closed" && isActive) return false;
    }
    return true;
  });

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const isFlowActive = (flow: Flow) => {
    return flow.state === "ACTIVE";
  };

  const handleRefresh = () => {
    setLoading(true);
    setError(null);
    loadFlowsData();
  };

  // Columns for DataTable
  const columns: ColumnDef<Flow>[] = [
    {
      id: "connection",
      header: "Connection",
      cell: (info) => (
        <div className="font-mono text-sm">
          {info.row.original.source_ip}:{info.row.original.source_port} → {info.row.original.destination_ip}:{info.row.original.destination_port}
        </div>
      ),
    },
    {
      id: "protocol",
      header: "Protocol",
      cell: (info) => (
        <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full border border-border bg-muted">
          {info.row.original.protocol}
        </span>
      ),
    },
    {
      id: "packets",
      header: "Packets",
      cell: (info) => <div className="text-right">{info.row.original.packets}</div>,
    },
    {
      id: "bytes",
      header: "Bytes",
      cell: (info) => <div className="text-right">{formatBytes(info.row.original.bytes)}</div>,
    },
    {
      id: "download",
      header: "Download",
      cell: (info) => (
        <div className="flex items-center justify-end">
          <ArrowDown className="h-4 w-4 mr-1 text-blue-500" />
          {formatBytes(info.row.original.download)}
        </div>
      ),
    },
    {
      id: "upload",
      header: "Upload",
      cell: (info) => (
        <div className="flex items-center justify-end">
          <ArrowUp className="h-4 w-4 mr-1 text-green-500" />
          {formatBytes(info.row.original.upload)}
        </div>
      ),
    },
    {
      id: "duration",
      header: "Duration",
      cell: (info) => {
        const flow = info.row.original;
        return (
          <div className="flex items-center gap-1">
            <Clock className="h-4 w-4 text-muted-foreground" />
            {Math.round((new Date(flow.last_seen).getTime() - new Date(flow.started_at).getTime()) / 1000)}s
          </div>
        );
      },
    },
    {
      id: "status",
      header: "Status",
      cell: (info) => {
        const isActive = isFlowActive(info.row.original);
        return (
          <StatusBadge variant={isActive ? "online" : "offline"} size="sm" dotOnly={false} pulse={isActive} />
        );
      },
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading flows data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-red-500">Unable to load flows</h2>
        <p className="text-muted-foreground mt-2">{error}</p>
        <button onClick={handleRefresh} className="mt-4 px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90 transition-colors">
          <RefreshCw className="h-4 w-4 mr-2 inline" />
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Network Flows</h1>
          <p className="text-muted-foreground">Monitor active network connections and data flows</p>
        </div>
        <button onClick={handleRefresh} disabled={loading} className="px-3 py-1.5 text-sm bg-primary text-white rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-2">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="card-default">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold">Filters</h3>
        </div>
        <div className="p-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <select 
              value={statusFilter} 
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-[180px] px-3 py-1.5 text-sm bg-background border border-border rounded-md"
            >
              <option value="all">All Flows</option>
              <option value="active">Active</option>
              <option value="closed">Closed</option>
            </select>
          </div>
        </div>
      </div>

      {/* Flows Table - Using new DataTable from design system */}
      <div className="card-default">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold">Network Flows ({filteredFlows.length})</h3>
          <p className="text-sm text-muted-foreground">Active and recent network connections between devices</p>
        </div>
        <DataTable<Flow>
          columns={columns}
          data={filteredFlows}
          enableSorting={true}
          enableFiltering={false}
          enablePagination={true}
          defaultPageSize={25}
          emptyMessage="No flows found"
        />
      </div>
    </div>
  );
}