"use client";

import { useCallback, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { DataTable } from "@/components/design-system";
import { StatusBadge } from "@/components/design-system";
import { Button } from "@/components/ui/button";
import { api, isAuthenticated } from "@/lib/api";
import { Quota } from "@/lib/types";
import { RefreshCw, Pause, Play, Trash2 } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";

export default function QuotasPage() {
  const router = useRouter();
  const [quotas, setQuotas] = useState<Quota[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadQuotasData = useCallback(async () => {
    try {
      const quotasData = await api.getQuotas();
      setQuotas(Array.isArray(quotasData) ? quotasData : []);
    } catch (err) {
      console.error("Failed to load quotas data:", err);
      setError(err instanceof Error ? err.message : "Failed to load quotas data");
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
      loadQuotasData();
    }, 0);

    return () => clearTimeout(timer);
  }, [router, loadQuotasData]);

  const handleToggleQuota = async (quota: Quota) => {
    if (!quota.id) return;
    try {
      await api.updateQuota(quota.id, { ...quota, enabled: !quota.enabled });
      await loadQuotasData();
    } catch (err) {
      console.error("Failed to toggle quota:", err);
      setError(err instanceof Error ? err.message : "Failed to toggle quota");
    }
  };

  const handleDeleteQuota = async (quotaId: string) => {
    if (!confirm("Are you sure you want to delete this quota?")) return;
    try {
      await api.deleteQuota(quotaId);
      await loadQuotasData();
    } catch (err) {
      console.error("Failed to delete quota:", err);
      setError(err instanceof Error ? err.message : "Failed to delete quota");
    }
  };

  const formatQuota = (quotaBytes?: number, dailyMb?: number, monthlyMb?: number) => {
    if (quotaBytes) {
      const mb = quotaBytes / 1024 / 1024;
      return `${mb.toFixed(2)} MB`;
    }
    if (dailyMb) return `${dailyMb} MB/day`;
    if (monthlyMb) return `${monthlyMb} MB/month`;
    return "—";
  };

  const handleRefresh = () => {
    setLoading(true);
    setError(null);
    loadQuotasData();
  };

  // Columns for DataTable
  const columns: ColumnDef<Quota>[] = [
    {
      id: "device",
      header: "Device",
      cell: (info) => (
        <div className="font-medium">{info.row.original.device_id}</div>
      ),
    },
    {
      id: "quota",
      header: "Quota",
      cell: (info) => (
        <div className="text-right">
          {formatQuota(info.row.original.quota_bytes, info.row.original.daily_quota_mb, info.row.original.monthly_quota_mb)}
        </div>
      ),
    },
    {
      id: "reset_day",
      header: "Reset Day",
      cell: (info) => <div className="text-right">{info.row.original.reset_day || 1}</div>,
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
        const quota = info.row.original;
        return (
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleToggleQuota(quota)}
            >
              {quota.enabled ? (
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
            {quota.id && (
              <Button
                size="sm"
                variant="destructive"
                onClick={() => handleDeleteQuota(quota.id!)}
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
          <p className="mt-4 text-muted-foreground">Loading quotas data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-red-500">Unable to load quotas</h2>
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
          <h1 className="text-3xl font-bold">Device Quotas</h1>
          <p className="text-muted-foreground">Manage data usage quotas for network devices</p>
        </div>
        <button onClick={handleRefresh} disabled={loading} className="px-3 py-1.5 text-sm bg-primary text-white rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-2">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Quotas Table - Using new DataTable from design system */}
      <div className="card-default">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold">Quotas ({quotas.length})</h3>
          <p className="text-sm text-muted-foreground">Data usage quotas applied to network devices</p>
        </div>
        <DataTable<Quota>
          columns={columns}
          data={quotas}
          enableSorting={false}
          enableFiltering={false}
          enablePagination={false}
          emptyMessage="No quotas found"
        />
      </div>
    </div>
  );
}