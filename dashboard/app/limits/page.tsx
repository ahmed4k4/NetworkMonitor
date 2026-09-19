"use client";

import { useCallback, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { DataTable } from "@/components/design-system";
import { StatusBadge } from "@/components/design-system";
import { Button } from "@/components/ui/button";
import { api, isAuthenticated } from "@/lib/api";
import { DeviceLimit } from "@/lib/types";
import { RefreshCw, Pause, Play, Trash2 } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";

export default function LimitsPage() {
  const router = useRouter();
  const [limits, setLimits] = useState<DeviceLimit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadLimitsData = useCallback(async () => {
    try {
      const limitsData = await api.getLimits();
      setLimits(Array.isArray(limitsData) ? limitsData : []);
    } catch (err) {
      console.error("Failed to load limits data:", err);
      setError(err instanceof Error ? err.message : "Failed to load limits data");
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
      loadLimitsData();
    }, 0);

    return () => clearTimeout(timer);
  }, [router, loadLimitsData]);

  const handleToggleLimit = async (limit: DeviceLimit) => {
    if (!limit.id) return;
    try {
      await api.updateLimit(limit.id, { ...limit, enabled: !limit.enabled });
      await loadLimitsData();
    } catch (err) {
      console.error("Failed to toggle limit:", err);
      setError(err instanceof Error ? err.message : "Failed to toggle limit");
    }
  };

  const handleDeleteLimit = async (limitId: string) => {
    if (!confirm("Are you sure you want to delete this limit?")) return;
    try {
      await api.deleteLimit(limitId);
      await loadLimitsData();
    } catch (err) {
      console.error("Failed to delete limit:", err);
      setError(err instanceof Error ? err.message : "Failed to delete limit");
    }
  };

  const handleRefresh = () => {
    setLoading(true);
    setError(null);
    loadLimitsData();
  };

  // Columns for DataTable
  const columns: ColumnDef<DeviceLimit>[] = [
    {
      id: "device",
      header: "Device",
      cell: (info) => (
        <div className="font-medium">{info.row.original.device_id}</div>
      ),
    },
    {
      id: "download_limit",
      header: "Download Limit",
      cell: (info) => (
        <div className="text-right">
          {info.row.original.download_limit ? `${info.row.original.download_limit} KB/s` : "—"}
        </div>
      ),
    },
    {
      id: "upload_limit",
      header: "Upload Limit",
      cell: (info) => (
        <div className="text-right">
          {info.row.original.upload_limit ? `${info.row.original.upload_limit} KB/s` : "—"}
        </div>
      ),
    },
    {
      id: "status",
      header: "Status",
      cell: (info) => (
        <StatusBadge variant={info.row.original.enabled ? "active" : "inactive"} size="sm" />
      ),
    },
    {
      id: "actions",
      header: "Actions",
      cell: (info) => {
        const limit = info.row.original;
        return (
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleToggleLimit(limit)}
            >
              {limit.enabled ? (
                <>
                  <Pause className="h-4 w-4 mr-1" />
                  Disable
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-1" />
                  Enable
                </>
              )}
            </Button>
            {limit.id && (
              <Button
                size="sm"
                variant="destructive"
                onClick={() => handleDeleteLimit(limit.id!)}
              >
                <Trash2 className="h-4 w-4 mr-1" />
                Delete
              </Button>
            )}
          </div>
        );
      },
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading limits data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-red-500">Unable to load limits</h2>
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
          <h1 className="text-3xl font-bold">Device Limits</h1>
          <p className="text-muted-foreground">Manage bandwidth limits for network devices</p>
        </div>
        <button onClick={handleRefresh} disabled={loading} className="px-3 py-1.5 text-sm bg-primary text-white rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-2">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Limits Table - Using new DataTable from design system */}
      <div className="card-default">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold">Limits ({limits.length})</h3>
          <p className="text-sm text-muted-foreground">Bandwidth limits applied to network devices</p>
        </div>
        <DataTable<DeviceLimit>
          columns={columns}
          data={limits}
          enableSorting={false}
          enableFiltering={false}
          enablePagination={false}
          emptyMessage="No limits found"
        />
      </div>
    </div>
  );
}