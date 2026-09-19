"use client";

import { useCallback, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { DataTable } from "@/components/design-system";
import { StatusBadge } from "@/components/design-system";
import { MetricCard } from "@/components/design-system";
import { Button } from "@/components/ui/button";
import { api, isAuthenticated } from "@/lib/api";
import { Alert } from "@/lib/types";
import { RefreshCw, AlertTriangle, AlertCircle, Clock, Info, Filter } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";

export default function AlertsPage() {
  const router = useRouter();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState("all");
  const [error, setError] = useState<string | null>(null);

  const loadAlertsData = useCallback(async () => {
    try {
      const alertsData = await api.getAlerts();
      setAlerts(Array.isArray(alertsData) ? alertsData : []);
    } catch (err) {
      console.error("Failed to load alerts data:", err);
      setError(err instanceof Error ? err.message : "Failed to load alerts data");
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
      loadAlertsData();
    }, 0);

    return () => clearTimeout(timer);
  }, [router, loadAlertsData]);

  const filteredAlerts = alerts.filter((alert) => {
    if (severityFilter !== "all" && alert.severity !== severityFilter) {
      return false;
    }
    return true;
  });

  const sortedAlerts = [...filteredAlerts].sort((a, b) =>
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const getSeverityVariant = (severity: string) => {
    switch (severity) {
      case "CRITICAL":
        return "danger";
      case "WARNING":
        return "warning";
      case "INFO":
        return "active";
      default:
        return "unknown";
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "CRITICAL":
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case "WARNING":
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case "INFO":
        return <Info className="h-4 w-4 text-blue-500" />;
      default:
        return <Info className="h-4 w-4 text-gray-500" />;
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  const handleRefresh = () => {
    setLoading(true);
    setError(null);
    loadAlertsData();
  };

  // Summary stats
  const criticalCount = alerts.filter((a) => a.severity === "CRITICAL").length;
  const warningCount = alerts.filter((a) => a.severity === "WARNING").length;
  const infoCount = alerts.filter((a) => a.severity === "INFO").length;

  // Columns for DataTable
  const columns: ColumnDef<Alert>[] = [
    {
      id: "message",
      header: "Alert",
      cell: (info) => (
        <div className="flex items-start gap-2">
          {getSeverityIcon(info.row.original.severity)}
          <div>
            <div className="font-medium">{info.row.original.message}</div>
            {info.row.original.device_id && (
              <div className="text-sm text-muted-foreground">
                Device: {info.row.original.device_id}
              </div>
            )}
          </div>
        </div>
      ),
    },
    {
      id: "type",
      header: "Type",
      cell: (info) => (
        <StatusBadge variant="active" size="xs" label={info.row.original.type} />
      ),
    },
    {
      id: "severity",
      header: "Severity",
      cell: (info) => (
        <StatusBadge variant={getSeverityVariant(info.row.original.severity)} size="sm" label={info.row.original.severity} />
      ),
    },
    {
      id: "timestamp",
      header: "Timestamp",
      cell: (info) => (
        <div className="flex items-center gap-1">
          <Clock className="h-4 w-4 text-muted-foreground" />
          {formatDate(info.row.original.created_at)}
        </div>
      ),
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading alerts data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-red-500">Unable to load alerts</h2>
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
          <h1 className="text-3xl font-bold">Network Alerts</h1>
          <p className="text-muted-foreground">Monitor and manage network security alerts and notifications</p>
        </div>
        <button onClick={handleRefresh} disabled={loading} className="px-3 py-1.5 text-sm bg-primary text-white rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-2">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="card-default">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </h3>
        </div>
        <div className="p-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <select 
              value={severityFilter} 
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="w-[180px] px-3 py-1.5 text-sm bg-background border border-border rounded-md"
            >
              <option value="all">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="WARNING">Warning</option>
              <option value="INFO">Info</option>
            </select>
          </div>
        </div>
      </div>

      {/* Alerts Summary Cards - Using new MetricCard from design system */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard 
          label="Critical Alerts" 
          value={criticalCount} 
          icon={<AlertCircle className="h-6 w-6" />} 
          variant="danger" 
        />
        <MetricCard 
          label="Warning Alerts" 
          value={warningCount} 
          icon={<AlertTriangle className="h-6 w-6" />} 
          variant="warning" 
        />
        <MetricCard 
          label="Info Alerts" 
          value={infoCount} 
          icon={<Info className="h-6 w-6" />} 
          variant="info" 
        />
        <MetricCard 
          label="Total Alerts" 
          value={alerts.length} 
          icon={<Clock className="h-6 w-6" />} 
          variant="primary" 
        />
      </div>

      {/* Alerts Table - Using new DataTable from design system */}
      <div className="card-default">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold">Alerts ({sortedAlerts.length})</h3>
          <p className="text-sm text-muted-foreground">Network security alerts and notifications</p>
        </div>
        <DataTable<Alert>
          columns={columns}
          data={sortedAlerts}
          enableSorting={false}
          enableFiltering={false}
          enablePagination={false}
          emptyMessage="No alerts found"
        />
      </div>
    </div>
  );
}