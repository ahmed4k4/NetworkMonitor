"use client";

import { useCallback, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { DataTable } from "@/components/design-system";
import { StatusBadge } from "@/components/design-system";
import { api, isAuthenticated } from "@/lib/api";
import { Device, WebSocketMessage } from "@/lib/types";
import { useWebSocket } from "@/hooks/useWebSocket";
import { ArrowUp, ArrowDown, RefreshCw, Search, Edit2, X } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { useToast } from "@/components/ui/toast";

export default function DevicesPage() {
  const router = useRouter();
  const { addToast } = useToast();
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [error, setError] = useState<string | null>(null);
  const [renameDialogOpen, setRenameDialogOpen] = useState(false);
  const [renameDeviceId, setRenameDeviceId] = useState<string | null>(null);
  const [renameInput, setRenameInput] = useState("");
  const [renaming, setRenaming] = useState(false);

  const loadDevices = useCallback(async () => {
    try {
      const data = await api.getDevices();
      setDevices(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load devices:", err);
      setError(err instanceof Error ? err.message : "Failed to load devices");
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
      loadDevices();
    }, 0);

    return () => clearTimeout(timer);
  }, [router, loadDevices]);

  // Handle real-time updates via WebSocket
  const handleMessage = useCallback((message: unknown) => {
    const msg = message as WebSocketMessage;

    if (msg?.type === "device_online" || msg?.type === "device_offline") {
      const data = msg.data as { device_id: string; ip?: string };

      setDevices((prevDevices) =>
        prevDevices.map((device) => {
          if (device.device_id === data.device_id) {
            return {
              ...device,
              state: msg.type === "device_online" ? "ONLINE" : "OFFLINE",
              ip: data.ip || device.ip,
            };
          }
          return device;
        }),
      );
    }

    // Real-time traffic updates with speed and usage data
    if (msg?.type === "traffic_update") {
      const data = msg.data as {
        device_id: string;
        download_speed_bps?: number;
        upload_speed_bps?: number;
        download_today?: number;
        upload_today?: number;
        total_today?: number;
      };

      if (data.device_id) {
        setDevices((prevDevices) =>
          prevDevices.map((device) => {
            if (device.device_id === data.device_id) {
              return {
                ...device,
                download_speed_bps: data.download_speed_bps ?? device.download_speed_bps,
                upload_speed_bps: data.upload_speed_bps ?? device.upload_speed_bps,
                current_speed_bps: ((data.download_speed_bps ?? 0) + (data.upload_speed_bps ?? 0)) || device.current_speed_bps,
                download_today: data.download_today ?? device.download_today,
                upload_today: data.upload_today ?? device.upload_today,
                total_today: data.total_today ?? device.total_today,
              };
            }
            return device;
          }),
        );
      }
    }
  }, []);

  useWebSocket(handleMessage);

  // Filter devices based on search and status
  const filteredDevices = devices.filter((device) => {
    const matchesSearch =
      device.custom_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.hostname?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.ip?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.mac.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.vendor?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === "all" || device.state === statusFilter;

    return matchesSearch && matchesStatus;
  });

  const getDisplayName = (device: Device): string => {
    return device.custom_name || device.hostname || "Unnamed Device";
  };

  const handleRenameClick = (device: Device) => {
    setRenameDeviceId(device.device_id);
    setRenameInput(device.custom_name || device.hostname || "");
    setRenameDialogOpen(true);
  };

  const handleRenameSubmit = async () => {
    if (!renameDeviceId || !renameInput.trim() || renaming) return;
    
    setRenaming(true);
    try {
      await api.renameDevice(renameDeviceId, renameInput.trim());
      setDevices((prevDevices) =>
        prevDevices.map((device) =>
          device.device_id === renameDeviceId
            ? { ...device, custom_name: renameInput.trim() }
            : device
        )
      );
      setRenameDialogOpen(false);
      setRenameDeviceId(null);
      setRenameInput("");
      addToast("Device renamed successfully", { variant: "success" });
    } catch (err) {
      console.error("Failed to rename device:", err);
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      addToast(`Failed to rename device: ${errorMessage}`, {
        variant: "danger"
      });
    } finally {
      setRenaming(false);
    }
  };

  const formatBytes = (bytes: number) => {
    if (!bytes || bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const formatSpeed = (bps?: number) => {
    if (!bps) return "0 Mbps";
    const mbps = bps / 1_000_000;
    if (mbps >= 1) return `${mbps.toFixed(2)} Mbps`;
    const kbps = bps / 1_000;
    if (kbps >= 1) return `${kbps.toFixed(2)} Kbps`;
    return `${bps} bps`;
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return "Never";
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  const handleRefresh = () => {
    setLoading(true);
    setError(null);
    loadDevices();
  };

  // Device status variant mapping
  const getStatusVariant = (state: string) => {
    switch (state) {
      case "ONLINE": return "online";
      case "OFFLINE": return "offline";
      default: return "unknown";
    }
  };

  const columns: ColumnDef<Device>[] = [
    {
      id: "name",
      header: "Name",
      cell: (info) => (
        <div className="flex items-center gap-2">
          <div className="flex flex-col">
            <div className="font-medium">{getDisplayName(info.row.original)}</div>
            <div className="text-sm text-muted-foreground">
              {info.row.original.custom_name && info.row.original.hostname && (
                <>
                  <span className="text-xs bg-gray-100 px-1 rounded">Custom</span>
                  <span className="text-xs text-muted-foreground ml-1">
                    (DHCP: {info.row.original.hostname})
                  </span>
                </>
              )}
              {!info.row.original.custom_name && info.row.original.vendor ? (
                <>{info.row.original.vendor || "Unknown Vendor"}</>
              ) : (
                info.row.original.vendor || "Unknown Vendor"
              )}
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 p-0 ml-1 hover:bg-primary/10"
            onClick={(e) => {
              e.stopPropagation();
              handleRenameClick(info.row.original);
            }}
            title="Rename device"
          >
            <Edit2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      ),
    },
    {
      id: "ip",
      header: "IP",
      cell: (info) => info.row.original.ip || "—",
    },
    {
      id: "mac",
      header: "MAC",
      cell: (info) => <span className="font-mono text-sm">{info.row.original.mac}</span>,
    },
    {
      id: "status",
      header: "Status",
      cell: (info) => (
        <StatusBadge variant={getStatusVariant(info.row.original.state)} size="sm" />
      ),
    },
    {
      id: "interface",
      header: "Interface",
      cell: (info) => info.row.original.interface || "Unknown",
    },
    {
      id: "download",
      header: "Download Today",
      cell: (info) => (
        <div className="flex items-center justify-end">
          <ArrowDown className="h-4 w-4 mr-1 text-blue-500" />
          {info.row.original.download_today != null 
            ? formatBytes(info.row.original.download_today) 
            : <span className="text-muted-foreground">—</span>}
        </div>
      ),
    },
    {
      id: "upload",
      header: "Upload Today",
      cell: (info) => (
        <div className="flex items-center justify-end">
          <ArrowUp className="h-4 w-4 mr-1 text-green-500" />
          {info.row.original.upload_today != null 
            ? formatBytes(info.row.original.upload_today) 
            : <span className="text-muted-foreground">—</span>}
        </div>
      ),
    },
    {
      id: "total",
      header: "Total Today",
      cell: (info) => {
        const downloadToday = info.row.original.download_today;
        const uploadToday = info.row.original.upload_today;
        if (downloadToday != null && uploadToday != null) {
          return <div className="text-right">{formatBytes(downloadToday + uploadToday)}</div>;
        }
        return <span className="text-muted-foreground">—</span>;
      },
    },
    {
      id: "speed",
      header: "Current Speed",
      cell: (info) => (
        <div className="flex items-center gap-1">
          <ArrowDown className="h-3 w-3 text-blue-500" />
          <span className="text-xs text-muted-foreground">
            {info.row.original.current_speed_bps != null 
              ? formatSpeed(info.row.original.current_speed_bps)
              : "—"}
          </span>
        </div>
      ),
    },
    {
      id: "quota",
      header: "Quota",
      cell: (info) => {
        const device = info.row.original;
        if (device.quota_bytes && device.quota_bytes > 0) {
          return (
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">
                {formatBytes(device.quota_remaining_bytes ?? 0)} left
              </span>
              <div className="h-2 w-24 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${(device.usage_percentage ?? 0) >= 90 ? "bg-red-500" : (device.usage_percentage ?? 0) >= 75 ? "bg-yellow-500" : "bg-blue-500"}`}
                  style={{ width: `${Math.min(100, device.usage_percentage ?? 0)}%` }}
                ></div>
              </div>
              <span className="text-xs">{device.usage_percentage?.toFixed(1)}%</span>
            </div>
          );
        }
        return <span className="text-xs text-muted-foreground">No quota set</span>;
      },
    },
    {
      id: "lastSeen",
      header: "Last Seen",
      cell: (info) => formatDate(info.row.original.last_seen),
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading devices...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-red-500">Unable to load devices</h2>
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
          <h1 className="text-3xl font-bold">Network Devices</h1>
          <p className="text-muted-foreground">Monitor all connected devices on your network</p>
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
            <div className="relative flex-1">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <input
                type="search"
                placeholder="Search devices..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8 w-full px-3 py-1.5 text-sm bg-background border border-border rounded-md"
              />
            </div>
            <select 
              value={statusFilter} 
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-[180px] px-3 py-1.5 text-sm bg-background border border-border rounded-md"
            >
              <option value="all">All Devices</option>
              <option value="ONLINE">Online</option>
              <option value="OFFLINE">Offline</option>
              <option value="UNKNOWN">Unknown</option>
            </select>
          </div>
        </div>
      </div>

      <DataTable<Device>
        columns={columns}
        data={filteredDevices}
        enableSorting={true}
        enableFiltering={false}
        enablePagination={true}
        defaultPageSize={25}
        onRowClick={(device) => router.push(`/devices/${device.device_id}`)}
        getRowId={(device) => device.device_id}
        striped={true}
        hoverable={true}
        showRowNumbers={false}
        emptyMessage="No devices found"
      />

      {/* Rename Dialog */}
      <Dialog open={renameDialogOpen} onOpenChange={setRenameDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Rename Device</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <label htmlFor="device-name" className="text-right text-sm font-medium">
                Name
              </label>
              <div className="col-span-3">
                <Input
                  id="device-name"
                  value={renameInput}
                  onChange={(e) => setRenameInput(e.target.value)}
                  placeholder="Enter device name"
                  autoFocus
                  disabled={renaming}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setRenameDialogOpen(false)}
              disabled={renaming}
            >
              Cancel
            </Button>
            <Button onClick={handleRenameSubmit} disabled={renaming || !renameInput.trim()}>
              {renaming ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
