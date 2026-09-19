"use client";

import { useCallback, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { DataTable } from "@/components/design-system";
import { MetricCard } from "@/components/design-system";
import { StatusBadge } from "@/components/design-system";
import { api, isAuthenticated } from "@/lib/api";
import { ProtocolStat } from "@/lib/types";
import { RefreshCw } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";

export default function ProtocolsPage() {
  const router = useRouter();
  const [protocols, setProtocols] = useState<ProtocolStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadProtocolsData = useCallback(async () => {
    try {
      const protocolsData = await api.getProtocols();
      setProtocols(Array.isArray(protocolsData) ? protocolsData : []);
    } catch (err) {
      console.error("Failed to load protocols data:", err);
      setError(err instanceof Error ? err.message : "Failed to load protocols data");
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
      loadProtocolsData();
    }, 0);

    return () => clearTimeout(timer);
  }, [router, loadProtocolsData]);

  const totalBytes = protocols.reduce((sum, stat) => sum + Number(stat.bytes || 0), 0);
  const totalPackets = protocols.reduce((sum, stat) => sum + Number(stat.packets || 0), 0);
  const totalConnections = protocols.reduce((sum, stat) => sum + Number(stat.connections || 0), 0);

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const handleRefresh = () => {
    setLoading(true);
    setError(null);
    loadProtocolsData();
  };

  // Columns for DataTable
  const columns: ColumnDef<ProtocolStat>[] = [
    {
      id: "protocol",
      header: "Protocol",
      cell: (info) => (
        <StatusBadge variant="active" size="sm" label={info.row.original.protocol} />
      ),
    },
    {
      id: "packets",
      header: "Packets",
      cell: (info) => <div className="text-right">{Number(info.row.original.packets || 0).toLocaleString()}</div>,
    },
    {
      id: "bytes",
      header: "Bytes",
      cell: (info) => <div className="text-right">{formatBytes(Number(info.row.original.bytes || 0))}</div>,
    },
    {
      id: "connections",
      header: "Connections",
      cell: (info) => <div className="text-right">{Number(info.row.original.connections || 0)}</div>,
    },
    {
      id: "percentage",
      header: "Percentage",
      cell: (info) => (
        <div className="text-right">
          {totalBytes > 0 ? ((Number(info.row.original.bytes || 0) / totalBytes) * 100).toFixed(1) : "0.0"}%
        </div>
      ),
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading protocols data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-red-500">Unable to load protocols</h2>
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
          <h1 className="text-3xl font-bold">Network Protocols</h1>
          <p className="text-muted-foreground">Protocol usage statistics from real network flows</p>
        </div>
        <button onClick={handleRefresh} disabled={loading} className="px-3 py-1.5 text-sm bg-primary text-white rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-2">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Summary Cards - Using new MetricCard from design system */}
      <div className="grid gap-4 sm:grid-cols-3">
        <MetricCard 
          label="Total Packets" 
          value={totalPackets.toLocaleString()} 
          variant="primary" 
        />
        <MetricCard 
          label="Total Bytes" 
          value={formatBytes(totalBytes)} 
          variant="success" 
        />
        <MetricCard 
          label="Active Connections" 
          value={totalConnections.toLocaleString()} 
          variant="info" 
        />
      </div>

      {/* Protocols Table - Using new DataTable from design system */}
      <div className="card-default">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold">Protocol Statistics</h3>
          <p className="text-sm text-muted-foreground">Packets, bytes, and connections per protocol</p>
        </div>
        <DataTable<ProtocolStat>
          columns={columns}
          data={protocols
            .slice()
            .sort((a, b) => Number(b.bytes || 0) - Number(a.bytes || 0))}
          enableSorting={false}
          enableFiltering={false}
          enablePagination={false}
          emptyMessage="No protocol data available"
        />
      </div>
    </div>
  );
}