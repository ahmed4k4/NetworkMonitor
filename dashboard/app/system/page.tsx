"use client";

import { useCallback, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { MetricCard } from "@/components/design-system";
import { StatusBadge } from "@/components/design-system";
import { Button } from "@/components/ui/button";
import { api, isAuthenticated } from "@/lib/api";
import { SystemStatus } from "@/lib/types";
import { RefreshCw, Server, Database, Activity, Cpu, LayoutDashboard, CheckCircle, AlertTriangle, XCircle } from "lucide-react";

export default function SystemPage() {
  const router = useRouter();
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSystemData = useCallback(async () => {
    try {
      const statusData = await api.getSystemStatus();
      setStatus(statusData);
    } catch (err) {
      console.error("Failed to load system status:", err);
      setError(err instanceof Error ? err.message : "Failed to load system status");
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
      loadSystemData();
    }, 0);

    return () => clearTimeout(timer);
  }, [router, loadSystemData]);

  const getStatusIcon = (status: string) => {
    const normalized = status.toLowerCase();
    if (normalized === "running" || normalized === "connected" || normalized === "healthy") {
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    }
    if (normalized === "degraded") {
      return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
    }
    return <XCircle className="h-5 w-5 text-red-500" />;
  };

  const getStatusLabel = (status: string) => {
    const normalized = status.toLowerCase();
    if (normalized === "running" || normalized === "connected" || normalized === "healthy") {
      return "Healthy";
    }
    if (normalized === "degraded") {
      return "Degraded";
    }
    return "Offline";
  };

  const getStatusVariant = (status: string) => {
    const normalized = status.toLowerCase();
    if (normalized === "running" || normalized === "connected" || normalized === "healthy") {
      return "online";
    }
    if (normalized === "degraded") {
      return "warning";
    }
    return "offline";
  };

  const handleRefresh = () => {
    setLoading(true);
    setError(null);
    loadSystemData();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading system status...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-red-500">Unable to load system status</h2>
        <p className="text-muted-foreground mt-2">{error}</p>
        <Button onClick={handleRefresh} className="mt-4">
          <RefreshCw className="h-4 w-4 mr-2" />
          Try Again
        </Button>
      </div>
    );
  }

  const components = status
    ? [
        { name: "Network Engine", status: status.engine, icon: Cpu },
        { name: "PostgreSQL", status: status.database, icon: Database },
        { name: "Packet Capture", status: status.capture, icon: Activity },
        { name: "FastAPI", status: status.api, icon: Server },
      ]
    : [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">System Status</h1>
          <p className="text-muted-foreground">Monitor the health of all system components</p>
        </div>
        <Button onClick={handleRefresh} disabled={loading} size="sm">
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* System Overview Cards - Using new MetricCard from design system */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {components.map((component) => (
          <MetricCard
            key={component.name}
            label={component.name}
            value={getStatusLabel(component.status)}
            icon={<component.icon className="h-6 w-6" />}
            variant={getStatusVariant(component.status) as "primary" | "success" | "warning" | "danger" | "info"}
          />
        ))}
      </div>

      {/* Component Health - Using design system card and StatusBadge */}
      <div className="card-default">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <LayoutDashboard className="h-5 w-5" />
            Component Health
          </h3>
          <p className="text-sm text-muted-foreground">Real-time status of all system components</p>
        </div>
        <div className="p-6">
          {components.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground">No system status available</p>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {components.map((component) => (
                <div
                  key={component.name}
                  className="flex items-center justify-between rounded-lg border border-border p-4"
                >
                  <div className="flex items-center gap-3">
                    <component.icon className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <div className="font-medium">{component.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {component.status}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(component.status)}
                    <StatusBadge 
                      variant={getStatusVariant(component.status)} 
                      size="sm" 
                      label={getStatusLabel(component.status)} 
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}