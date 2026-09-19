"use client";

import { useCallback, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { DataTable } from "@/components/design-system";
import { api, isAuthenticated } from "@/lib/api";
import { TrafficSample, Device } from "@/lib/types";
import { ArrowUp, ArrowDown, RefreshCw, Search, Filter } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";

export default function TrafficPage() {
  const router = useRouter();
  const [trafficData, setTrafficData] = useState<TrafficSample[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [deviceFilter, setDeviceFilter] = useState("all");
  const [error, setError] = useState<string | null>(null);

  const loadTrafficData = useCallback(async () => {
    try {
      const [trafficResult, devicesResult] = await Promise.allSettled([
        api.getTraffic(),
        api.getDevices(),
      ]);

      if (trafficResult.status === "fulfilled") {
        setTrafficData(trafficResult.value);
      } else {
        console.warn("[Traffic] Could not fetch traffic data:", trafficResult.reason);
        setTrafficData([]);
      }

      if (devicesResult.status === "fulfilled") {
        setDevices(devicesResult.value);
      } else {
        console.warn("[Devices] Could not fetch devices list:", devicesResult.reason);
        setDevices([]);
      }
    } catch (err) {
      console.error("Failed to load traffic data:", err);
      setError(err instanceof Error ? err.message : "Failed to load traffic data");
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
      loadTrafficData();
    }, 0);

    return () => clearTimeout(timer);
  }, [router, loadTrafficData]);

  const filteredTraffic = trafficData.filter((sample) => {
    if (deviceFilter !== "all" && sample.device_id !== deviceFilter) {
      return false;
    }

    if (searchTerm) {
      const device = devices.find((d) => d.device_id === sample.device_id);
      const matchesDevice =
        device?.hostname?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        device?.ip.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesIp = sample.ip.toLowerCase().includes(searchTerm.toLowerCase());

      if (!matchesDevice && !matchesIp) {
        return false;
      }
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
    loadTrafficData();
  };

  // Columns for DataTable
  const columns: ColumnDef<TrafficSample>[] = [
    {
      id: "device",
      header: "Device",
      cell: (info) => {
        const sample = info.row.original;
        const device = devices.find((d) => d.device_id === sample.device_id);
        return (
          <div>
            <div className="font-medium">{device?.hostname || "Unnamed Device"}</div>
            <div className="text-sm text-muted-foreground">{device?.vendor || "Unknown Vendor"}</div>
          </div>
        );
      },
    },
    {
      id: "ip",
      header: "IP Address",
      cell: (info) => <span className="font-mono">{info.row.original.ip}</span>,
    },
    {
      id: "time",
      header: "Time",
      cell: (info) => formatDate(info.row.original.time),
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
      id: "packets",
      header: "Packets",
      cell: (info) => <div className="text-right">{info.row.original.packets}</div>,
    },
    {
      id: "connections",
      header: "Connections",
      cell: (info) => <div className="text-right">{info.row.original.connections}</div>,
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading traffic data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-red-500">Unable to load traffic data</h2>
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
          <h1 className="text-3xl font-bold">Network Traffic</h1>
          <p className="text-muted-foreground">
            Monitor network traffic and connections
          </p>
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
            <div className="relative flex-1">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <input
                type="search"
                placeholder="Search devices or IPs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8 w-full px-3 py-1.5 text-sm bg-background border border-border rounded-md"
              />
            </div>
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

      {/* Traffic Table - Using new DataTable from design system */}
      <div className="card-default">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold">Network Traffic ({filteredTraffic.length} entries)</h3>
          <p className="text-sm text-muted-foreground">Real-time network traffic data for all devices</p>
        </div>
        <DataTable<TrafficSample>
          columns={columns}
          data={filteredTraffic}
          enableSorting={true}
          enableFiltering={false}
          enablePagination={true}
          defaultPageSize={25}
          emptyMessage="No traffic data found"
        />
      </div>
    </div>
  );
}