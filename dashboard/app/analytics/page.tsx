"use client";

import { useCallback, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { MetricCard } from "@/components/design-system";
import { DataTable } from "@/components/design-system";
import { StatusBadge } from "@/components/design-system";
import type { ColumnDef } from "@tanstack/react-table";
import TrafficChart from "@/components/dashboard/TrafficChart";
import { api, isAuthenticated } from "@/lib/api";
import { Device, TrafficSample, TopDevice, AnalyticsEntry } from "@/lib/types";
import { ArrowUp, ArrowDown, RefreshCw, TrendingUp, Wifi, Search, ChevronLeft, ChevronRight } from "lucide-react";

export default function AnalyticsPage() {
  const router = useRouter();
  const [devices, setDevices] = useState<Device[]>([]);
  const [traffic, setTraffic] = useState<TrafficSample[]>([]);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsEntry[]>([]);
  const [topDevices, setTopDevices] = useState<TopDevice[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState("day");
  const [error, setError] = useState<string | null>(null);

  const loadAnalyticsData = useCallback(async () => {
    try {
      const [devicesResult, trafficResult, topDevicesResult] = await Promise.allSettled([
        api.getDevices(),
        api.getAnalytics(timeRange),
        api.getTopDevices(),
      ]);

      if (devicesResult.status === "fulfilled") {
        setDevices(devicesResult.value);
      } else {
        console.warn("[Analytics] Failed to load devices:", devicesResult.reason);
        setDevices([]);
      }

      if (trafficResult.status === "fulfilled") {
        setAnalyticsData(trafficResult.value);
      } else {
        console.warn("[Analytics] Failed to load traffic:", trafficResult.reason);
        setAnalyticsData([]);
      }

      if (topDevicesResult.status === "fulfilled") {
        setTopDevices(topDevicesResult.value);
      } else {
        console.warn("[Analytics] Failed to load top devices:", topDevicesResult.reason);
        setTopDevices([]);
      }
    } catch (err) {
      console.error("Failed to load analytics data:", err);
      setError(err instanceof Error ? err.message : "Failed to load analytics data");
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }

    const timer = setTimeout(() => {
      loadAnalyticsData();
    }, 0);

    return () => clearTimeout(timer);
  }, [router, loadAnalyticsData]);

  // Build chart data from real speed_bps from traffic samples
  const chartData = traffic
    .slice()
    .sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime())
    .map((sample) => ({
      time: new Date(sample.time).toLocaleTimeString(),
      download: Number(sample.download_speed_bps ?? 0) / 1_000_000,
      upload: Number(sample.upload_speed_bps ?? 0) / 1_000_000,
    }));

  // Today's totals from usage_daily (real per-device today data)
  const totalDownload = devices.reduce(
    (sum, device) => sum + Number(device.download_today ?? (device.download || 0)),
    0,
  );
  const totalUpload = devices.reduce(
    (sum, device) => sum + Number(device.upload_today ?? (device.upload || 0)),
    0,
  );
  const onlineDevices = devices.filter((device) => device.state === "ONLINE").length;
  const offlineDevices = devices.filter((device) => device.state === "OFFLINE").length;

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
    loadAnalyticsData();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading analytics data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-red-500">Unable to load analytics</h2>
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
          <h1 className="text-3xl font-bold">Network Analytics</h1>
          <p className="text-muted-foreground">Comprehensive network traffic and usage statistics</p>
        </div>
        <div className="flex items-center gap-2">
          <select 
            value={timeRange} 
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-1.5 text-sm bg-background border border-border rounded-md"
          >
            <option value="hour">Last Hour</option>
            <option value="day">Last 24 Hours</option>
            <option value="week">Last Week</option>
            <option value="month">Last Month</option>
          </select>
          <button onClick={handleRefresh} disabled={loading} className="px-3 py-1.5 text-sm bg-primary text-white rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-2">
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Statistics Cards - Using new MetricCard from design system */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard 
          label="Total Download" 
          value={formatBytes(totalDownload)} 
          icon={<ArrowDown className="h-6 w-6" />} 
          variant="primary" 
        />
        <MetricCard 
          label="Total Upload" 
          value={formatBytes(totalUpload)} 
          icon={<ArrowUp className="h-6 w-6" />} 
          variant="success" 
        />
        <MetricCard 
          label="Online Devices" 
          value={onlineDevices} 
          icon={<Wifi className="h-6 w-6" />} 
          variant="info" 
        />
        <MetricCard 
          label="Offline Devices" 
          value={offlineDevices} 
          icon={<TrendingUp className="h-6 w-6" />} 
          variant="warning" 
        />
      </div>

      {/* Traffic Chart */}
      <div className="card-default">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold">Traffic Overview</h3>
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

      {/* Top Devices Table - Using new DataTable from design system */}
      <div className="card-default">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold">Top Devices by Traffic</h3>
          <p className="text-sm text-muted-foreground">Devices consuming the most network bandwidth</p>
        </div>
        {topDevices.length === 0 ? (
          <div className="p-6 text-center text-muted-foreground">
            No device data available
          </div>
        ) : (
          <DataTable<TopDevice>
            columns={[
              {
                id: "rank",
                header: "#",
                cell: (info) => (
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs">
                    {info.row.index + 1}
                  </div>
                ),
              },
              {
                id: "device",
                header: "Device",
                cell: (info) => (
                  <div className="flex items-center gap-3">
                    <div className="font-medium">{info.row.original.device_id}</div>
                    <div className="text-sm text-muted-foreground">{info.row.original.ip}</div>
                  </div>
                ),
              },
              {
                id: "download",
                header: "Download",
                cell: (info) => (
                  <div className="flex items-center gap-1">
                    <ArrowDown className="h-4 w-4 text-blue-500" />
                    <span>{formatBytes(info.row.original.download)}</span>
                  </div>
                ),
              },
              {
                id: "upload",
                header: "Upload",
                cell: (info) => (
                  <div className="flex items-center gap-1">
                    <ArrowUp className="h-4 w-4 text-green-500" />
                    <span>{formatBytes(info.row.original.upload)}</span>
                  </div>
                ),
              },
            ]}
            data={topDevices.slice(0, 10)}
            enableSorting={false}
            enableFiltering={false}
            enablePagination={false}
          />
        )}
      </div>
    </div>
  );
}