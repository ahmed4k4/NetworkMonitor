"use client";

import { useCallback, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { DataTable } from "@/components/design-system";
import { StatusBadge } from "@/components/design-system";
import TrafficChart from "@/components/dashboard/TrafficChart";
import { api, isAuthenticated } from "@/lib/api";
import { Device, TrafficSample, AnalyticsEntry } from "@/lib/types";
import { ArrowUp, ArrowDown, RefreshCw, Filter } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";

export default function HistoryPage() {
  const router = useRouter();
  const [devices, setDevices] = useState<Device[]>([]);
  const [trafficData, setTrafficData] = useState<AnalyticsEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState("7days");
  const [deviceFilter, setDeviceFilter] = useState("all");
  const [error, setError] = useState<string | null>(null);

  const loadHistoryData = useCallback(async () => {
    try {
      const [devicesResult, trafficResult] = await Promise.allSettled([
        api.getDevices(),
        api.getAnalytics("day"),
      ]);

      if (devicesResult.status === "fulfilled") {
        setDevices(devicesResult.value);
      } else {
        console.warn("[History] Failed to load devices:", devicesResult.reason);
        setDevices([]);
      }

      if (trafficResult.status === "fulfilled") {
        setTrafficData(trafficResult.value);
      } else {
        console.warn("[History] Failed to load traffic:", trafficResult.reason);
        setTrafficData([]);
      }
    } catch (err) {
      console.error("Failed to load history data:", err);
      setError(err instanceof Error ? err.message : "Failed to load history data");
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
      loadHistoryData();
    }, 0);

    return () => clearTimeout(timer);
  }, [router, loadHistoryData]);

  // Build chart data from real usage_daily data (bytes per day)
  const chartData = trafficData
    .slice()
    .sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime())
    .map((sample) => ({
      time: new Date(sample.time).toLocaleString(),
      download: Number(sample.download || 0) / 1024 / 1024,
      upload: Number(sample.upload || 0) / 1024 / 1024,
    }));

  // Aggregate traffic by device using real today's usage from devices API
  const deviceSummary = devices.map((device) => {
    const download = Number(device.download_today ?? (device.download || 0));
    const upload = Number(device.upload_today ?? (device.upload || 0));

    return {
      device,
      download,
      upload,
      total: download + upload,
    };
  });

  const filteredSummary = deviceFilter === "all"
    ? deviceSummary
    : deviceSummary.filter((item) => item.device.device_id === deviceFilter);

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
    loadHistoryData();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading history data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-red-500">Unable to load history</h2>
        <p className="text-muted-foreground mt-2">{error}</p>
        <button onClick={handleRefresh} className="mt-4 px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90 transition-colors">
          <RefreshCw className="h-4 w-4 mr-2 inline" />
          Try Again
        </button>
      </div>
    );
  }

  // Columns for the DataTable
  const columns: ColumnDef<typeof filteredSummary[0]>[] = [
    {
      id: "device",
      header: "Device",
      cell: (info) => (
        <div>
          <div className="font-medium">{info.row.original.device.hostname || "Unnamed Device"}</div>
          <div className="text-sm text-muted-foreground">{info.row.original.device.ip}</div>
        </div>
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
    {
      id: "total",
      header: "Total",
      cell: (info) => (
        <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full border border-border bg-muted">
          {formatBytes(info.row.original.total)}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Network History</h1>
          <p className="text-muted-foreground">Historical network traffic and usage patterns</p>
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
              value={dateRange} 
              onChange={(e) => setDateRange(e.target.value)}
              className="w-[180px] px-3 py-1.5 text-sm bg-background border border-border rounded-md"
            >
              <option value="7days">Last 7 Days</option>
              <option value="30days">Last 30 Days</option>
              <option value="90days">Last 90 Days</option>
            </select>
            <select 
              value={deviceFilter} 
              onChange={(e) => setDeviceFilter(e.target.value)}
              className="w-[180px] px-3 py-1.5 text-sm bg-background border border-border rounded-md"
            >
              <option value="all">All Devices</option>
              {devices.map((device) => (
                <option key={device.device_id} value={device.device_id}>
                  {device.hostname || device.ip}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Historical Traffic Chart */}
      <div className="card-default">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold">Traffic History</h3>
          <p className="text-sm text-muted-foreground">Network traffic from real API data</p>
        </div>
        <div className="p-6">
          {chartData.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              No traffic data available
            </div>
          ) : (
            <TrafficChart data={chartData} />
          )}
        </div>
      </div>

      {/* Historical Data Table - Using new DataTable from design system */}
      <div className="card-default">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold">Usage by Device</h3>
          <p className="text-sm text-muted-foreground">Cumulative network usage for each device</p>
        </div>
        {filteredSummary.length === 0 ? (
          <div className="p-6 text-center text-muted-foreground">
            No historical data found
          </div>
        ) : (
          <DataTable<typeof filteredSummary[0]>
            columns={columns}
            data={filteredSummary.sort((a, b) => b.total - a.total)}
            enableSorting={false}
            enableFiltering={false}
            enablePagination={false}
            emptyMessage="No historical data found"
          />
        )}
      </div>
    </div>
  );
}