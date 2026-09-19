"use client";

import { useCallback, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { DataTable } from "@/components/design-system";
import { StatusBadge } from "@/components/design-system";
import { MetricCard } from "@/components/design-system";
import { api, isAuthenticated } from "@/lib/api";
import { NetworkInterface } from "@/lib/types";
import { RefreshCw, ArrowUp, ArrowDown, Network } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";

export default function InterfacesPage() {
  const router = useRouter();
  const [interfaces, setInterfaces] = useState<NetworkInterface[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadInterfacesData = useCallback(async () => {
    try {
      const interfacesData = await api.getInterfaces();
      setInterfaces(Array.isArray(interfacesData) ? interfacesData : []);
    } catch (err) {
      console.error("Failed to load interfaces data:", err);
      setError(err instanceof Error ? err.message : "Failed to load interfaces data");
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
      loadInterfacesData();
    }, 0);

    return () => clearTimeout(timer);
  }, [router, loadInterfacesData]);

  const formatBytes = (bytes?: number) => {
    if (!bytes) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const handleRefresh = () => {
    setLoading(true);
    setError(null);
    loadInterfacesData();
  };

  // Summary stats
  const totalInterfaces = interfaces.length;
  const upInterfaces = interfaces.filter((i) => i.status === "UP").length;
  const totalDownload = interfaces.reduce((sum, i) => sum + Number(i.download || 0), 0);
  const totalUpload = interfaces.reduce((sum, i) => sum + Number(i.upload || 0), 0);

  // Columns for DataTable
  const columns: ColumnDef<NetworkInterface>[] = [
    {
      id: "name",
      header: "Interface",
      cell: (info) => (
        <div>
          <div className="flex items-center gap-2">
            <Network className="h-4 w-4 text-muted-foreground" />
            <span className="font-medium">{info.row.original.name}</span>
          </div>
          {info.row.original.description && (
            <div className="text-sm text-muted-foreground">{info.row.original.description}</div>
          )}
        </div>
      ),
    },
    {
      id: "type",
      header: "Type",
      cell: (info) => (
        <StatusBadge variant="active" size="xs" label={info.row.original.type || "UNKNOWN"} />
      ),
    },
    {
      id: "status",
      header: "Status",
      cell: (info) => (
        <StatusBadge variant={info.row.original.status === "UP" ? "online" : "offline"} size="sm" />
      ),
    },
    {
      id: "ip",
      header: "IP Address",
      cell: (info) => (
        <span className="font-mono text-sm">{info.row.original.ip || "—"}</span>
      ),
    },
    {
      id: "mac",
      header: "MAC",
      cell: (info) => (
        <span className="font-mono text-sm">{info.row.original.mac || "—"}</span>
      ),
    },
    {
      id: "speed",
      header: "Speed",
      cell: (info) => (
        <span>{info.row.original.speed ? `${info.row.original.speed} Mbps` : "—"}</span>
      ),
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
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading interfaces data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-red-500">Unable to load interfaces</h2>
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
          <h1 className="text-3xl font-bold">Network Interfaces</h1>
          <p className="text-muted-foreground">Monitor network interface status and traffic</p>
        </div>
        <button onClick={handleRefresh} disabled={loading} className="px-3 py-1.5 text-sm bg-primary text-white rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-2">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Summary Cards - Using new MetricCard from design system */}
      <div className="grid gap-4 sm:grid-cols-4">
        <MetricCard 
          label="Total Interfaces" 
          value={totalInterfaces} 
          icon={<Network className="h-6 w-6" />} 
          variant="primary" 
        />
        <MetricCard 
          label="Interfaces Up" 
          value={upInterfaces} 
          icon={<Network className="h-6 w-6" />} 
          variant="success" 
        />
        <MetricCard 
          label="Total Download" 
          value={formatBytes(totalDownload)} 
          icon={<ArrowDown className="h-6 w-6" />} 
          variant="info" 
        />
        <MetricCard 
          label="Total Upload" 
          value={formatBytes(totalUpload)} 
          icon={<ArrowUp className="h-6 w-6" />} 
          variant="warning" 
        />
      </div>

      {/* Interfaces Table - Using new DataTable from design system */}
      <div className="card-default">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold">Interfaces ({interfaces.length})</h3>
          <p className="text-sm text-muted-foreground">Network interfaces detected by the system</p>
        </div>
        <DataTable<NetworkInterface>
          columns={columns}
          data={interfaces}
          enableSorting={false}
          enableFiltering={false}
          enablePagination={false}
          emptyMessage="No interfaces found"
        />
      </div>
    </div>
  );
}