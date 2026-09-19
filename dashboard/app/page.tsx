"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { Activity, ArrowDown, ArrowUp, Network, Server } from "lucide-react";

import { MetricCard } from "@/components/design-system";
import TrafficChart from "@/components/dashboard/TrafficChart";

import { api, isAuthenticated } from "@/lib/api";
import { useWebSocket } from "@/hooks/useWebSocket";

import type { Device, TrafficSample, SystemStatus } from "@/lib/types";

export default function Dashboard() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [devices, setDevices] = useState<Device[]>([]);
  const [traffic, setTraffic] = useState<TrafficSample[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);

  /*
   * Initial Data
   */
  useEffect(() => {
    // Check if user is authenticated
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }

    const loadData = async () => {
      setLoading(true);
      setError(null);

      try {
        const [devicesData, trafficData, systemData] = await Promise.allSettled([
          api.getDevices(),
          api.getTraffic(),
          api.getSystemStatus(),
        ]);

        if (devicesData.status === "fulfilled") {
          setDevices(devicesData.value);
        } else {
          console.warn("[Dashboard] Failed to load devices:", devicesData.reason);
        }

        if (trafficData.status === "fulfilled") {
          setTraffic(trafficData.value);
        } else {
          console.warn("[Dashboard] Failed to load traffic:", trafficData.reason);
        }

        if (systemData.status === "fulfilled") {
          setSystemStatus(systemData.value);
        } else {
          console.warn("[Dashboard] Failed to load system status:", systemData.reason);
        }

      } catch (err) {
        console.error("[Dashboard] Failed to load data:", err);
        setError(err instanceof Error ? err.message : "Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [router]);

  /*
   * WebSocket Live Updates
   */
  const handleMessage = useCallback((message: unknown) => {
    const msg = message as {
      type?: string;
      data?: Record<string, unknown>;
    };

    if (!msg?.type) return;

    // Traffic Update
    if (msg.type === "traffic_update") {
      const data = msg.data || {};

      setTraffic((previous) => {
        const newSample: TrafficSample = {
          device_id: String(data.device_id || ""),
          ip: String(data.ip || ""),
          time: String(data.timestamp || new Date().toISOString()),
          download: Number(data.download || 0),
          upload: Number(data.upload || 0),
          packets: Number(data.packets || 0),
          connections: Number(data.connections || 0),
          download_speed_bps: Number(data.download_speed_bps || 0),
          upload_speed_bps: Number(data.upload_speed_bps || 0),
        };

        return [...previous, newSample].slice(-60);
      });

      // Also update device usage data in real-time
      const deviceId = String(data.device_id || "");
      if (deviceId) {
        setDevices((previous) =>
          previous.map((device) =>
            device.device_id === deviceId
              ? {
                  ...device,
                  download_today: Number(data.download_today ?? device.download_today),
                  upload_today: Number(data.upload_today ?? device.upload_today),
                  total_today: Number(data.total_today ?? device.total_today),
                  download_speed_bps: Number(data.download_speed_bps ?? device.download_speed_bps),
                  upload_speed_bps: Number(data.upload_speed_bps ?? device.upload_speed_bps),
                  current_speed_bps: ((Number(data.download_speed_bps ?? 0) + Number(data.upload_speed_bps ?? 0))) || device.current_speed_bps,
                }
              : device,
          ),
        );
      }
    }

    // Device Online
    if (msg.type === "device_online") {
      const data = msg.data || {};

      setDevices((previous) => {
        const deviceId = String(data.device_id || "");
        const exists = previous.some((d) => d.device_id === deviceId);

        if (exists) {
          return previous.map((device) =>
            device.device_id === deviceId
              ? { ...device, state: "ONLINE", ip: String(data.ip || device.ip) }
              : device,
          );
        }

        // New device discovered via WebSocket
        return [
          ...previous,
          {
            device_id: deviceId,
            mac: String(data.mac || ""),
            ip: String(data.ip || ""),
            hostname: String(data.hostname || ""),
            vendor: String(data.vendor || ""),
            state: "ONLINE" as const,
            upload: 0,
            download: 0,
          },
        ];
      });
    }

    // Device Offline
    if (msg.type === "device_offline") {
      const data = msg.data || {};

      setDevices((previous) =>
        previous.map((device) =>
          device.device_id === String(data.device_id || "")
            ? { ...device, state: "OFFLINE" }
            : device,
        ),
      );
    }

    // System Status Update - real-time dashboard stats
    if (msg.type === "system_status") {
      const data = msg.data || {};
      
      setSystemStatus((prev) => ({
        engine: prev?.engine || "running",
        database: prev?.database || "connected",
        capture: prev?.capture || "running",
        api: prev?.api || "running",
        total_devices: Number(data.total_devices ?? prev?.total_devices ?? 0),
        online_devices: Number(data.online_devices ?? prev?.online_devices ?? 0),
        offline_devices: Number(data.offline_devices ?? prev?.offline_devices ?? 0),
        active_connections: Number(data.active_connections ?? prev?.active_connections ?? 0),
        active_flows: Number(data.active_flows ?? prev?.active_flows ?? 0),
        total_download: prev?.total_download ?? 0,
        total_upload: prev?.total_upload ?? 0,
        today_download: prev?.today_download ?? 0,
        today_upload: prev?.today_upload ?? 0,
        current_download_speed_bps: Number(data.current_download_speed_bps ?? prev?.current_download_speed_bps ?? 0),
        current_upload_speed_bps: Number(data.current_upload_speed_bps ?? prev?.current_upload_speed_bps ?? 0),
        current_speed_bps: Number(data.current_speed_bps ?? prev?.current_speed_bps ?? 0),
        peak_bandwidth_bps: Number(data.peak_bandwidth_bps ?? prev?.peak_bandwidth_bps ?? 0),
      }));
    }
  }, []);

  useWebSocket(handleMessage);

  /*
   * Statistics - all from real backend data
   */
  const onlineDevices = systemStatus?.online_devices ?? devices.filter((device) => device.state === "ONLINE").length;

  // Today's totals from usage_daily (real per-device today data)
  const totalDownload = devices.reduce(
    (sum, device) => sum + Number(device.download_today ?? (device.download || 0)),
    0,
  );

  const totalUpload = devices.reduce(
    (sum, device) => sum + Number(device.upload_today ?? (device.upload || 0)),
    0,
  );

  // Active connections from connections table (real current count)
  const activeConnections = systemStatus?.active_connections ?? 0;

  // Peak bandwidth from traffic_samples (real bps)
  const peakBandwidth = systemStatus?.peak_bandwidth_bps ?? 0;

  // Current speed from system status (real bps)
  const currentSpeed = systemStatus?.current_speed_bps ?? 0;

  /*
   * Chart Data - use real speed_bps from traffic samples
   */
  const chartData = traffic
    .slice()
    .sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime())
    .map((item) => ({
      time: new Date(item.time).toLocaleTimeString(),
      download: Number(item.download_speed_bps ?? 0) / 1_000_000,
      upload: Number(item.upload_speed_bps ?? 0) / 1_000_000,
    }));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-red-500">Unable to load dashboard</h2>
        <p className="text-muted-foreground mt-2">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold">Network Overview</h1>
        <p className="text-muted-foreground">Real-time network monitoring</p>
      </div>

      {/* Statistics - Using new MetricCard from design system */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <MetricCard 
          label="Total Download Today" 
          value={`${(totalDownload / 1024 / 1024).toFixed(2)} MB`} 
          icon={<ArrowDown className="h-6 w-6" />} 
          variant="primary" 
        />
        <MetricCard 
          label="Total Upload Today" 
          value={`${(totalUpload / 1024 / 1024).toFixed(2)} MB`} 
          icon={<ArrowUp className="h-6 w-6" />} 
          variant="success" 
        />
        <MetricCard 
          label="Online Devices" 
          value={onlineDevices} 
          icon={<Network className="h-6 w-6" />} 
          variant="info" 
        />
        <MetricCard 
          label="Active Connections" 
          value={activeConnections} 
          icon={<Activity className="h-6 w-6" />} 
          variant="warning" 
        />
        <MetricCard 
          label="Current Speed" 
          value={`${(currentSpeed / 1_000_000).toFixed(2)} Mbps`} 
          icon={<Server className="h-6 w-6" />} 
          variant="neutral" 
        />
      </div>

      {/* Live Traffic */}
      <div className="card-default">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold">Live Traffic</h3>
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
    </div>
  );
}