"use client";

import { useCallback, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { DataTable } from "@/components/design-system";
import { StatusBadge } from "@/components/design-system";
import { Button } from "@/components/ui/button";
import { api, isAuthenticated } from "@/lib/api";
import { FirewallRule } from "@/lib/types";
import { RefreshCw, Pause, Play, Trash2, Shield } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";

export default function FirewallPage() {
  const router = useRouter();
  const [rules, setRules] = useState<FirewallRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadFirewallData = useCallback(async () => {
    try {
      const rulesData = await api.getFirewall();
      setRules(Array.isArray(rulesData) ? rulesData : []);
    } catch (err) {
      console.error("Failed to load firewall data:", err);
      setError(err instanceof Error ? err.message : "Failed to load firewall data");
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
      loadFirewallData();
    }, 0);

    return () => clearTimeout(timer);
  }, [router, loadFirewallData]);

  const handleToggleRule = async (rule: FirewallRule) => {
    if (!rule.id) return;
    try {
      await api.updateFirewallRule(rule.id, { ...rule, enabled: !rule.enabled });
      await loadFirewallData();
    } catch (err) {
      console.error("Failed to toggle firewall rule:", err);
      setError(err instanceof Error ? err.message : "Failed to toggle firewall rule");
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!confirm("Are you sure you want to delete this firewall rule?")) return;
    try {
      await api.deleteFirewallRule(ruleId);
      await loadFirewallData();
    } catch (err) {
      console.error("Failed to delete firewall rule:", err);
      setError(err instanceof Error ? err.message : "Failed to delete firewall rule");
    }
  };

  const getActionVariant = (action: string) => {
    switch (action) {
      case "ALLOW":
        return "success";
      case "BLOCK":
        return "danger";
      case "DROP":
        return "warning";
      default:
        return "active";
    }
  };

  const handleRefresh = () => {
    setLoading(true);
    setError(null);
    loadFirewallData();
  };

  // Columns for DataTable
  const columns: ColumnDef<FirewallRule>[] = [
    {
      id: "name",
      header: "Name",
      cell: (info) => (
        <div>
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-muted-foreground" />
            <span className="font-medium">{info.row.original.name}</span>
          </div>
          {info.row.original.description && (
            <div className="text-sm text-muted-foreground">{info.row.original.description}</div>
          )}
        </div>
      ),
    },
    {
      id: "action",
      header: "Action",
      cell: (info) => {
        const action = info.row.original.action;
        const variant = getActionVariant(action);
        return (
          <StatusBadge variant={variant} size="sm" label={action} />
        );
      },
    },
    {
      id: "source",
      header: "Source",
      cell: (info) => (
        <span className="font-mono text-sm">{info.row.original.source || "*"}</span>
      ),
    },
    {
      id: "destination",
      header: "Destination",
      cell: (info) => (
        <span className="font-mono text-sm">{info.row.original.destination || "*"}</span>
      ),
    },
    {
      id: "protocol",
      header: "Protocol",
      cell: (info) => <span>{info.row.original.protocol || "*"}</span>,
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
        const rule = info.row.original;
        return (
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleToggleRule(rule)}
            >
              {rule.enabled ? (
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
            {rule.id && (
              <Button
                size="sm"
                variant="destructive"
                onClick={() => handleDeleteRule(rule.id!)}
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
          <p className="mt-4 text-muted-foreground">Loading firewall data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-red-500">Unable to load firewall rules</h2>
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
          <h1 className="text-3xl font-bold">Firewall Rules</h1>
          <p className="text-muted-foreground">Manage network firewall rules and policies</p>
        </div>
        <button onClick={handleRefresh} disabled={loading} className="px-3 py-1.5 text-sm bg-primary text-white rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-2">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Firewall Rules Table - Using new DataTable from design system */}
      <div className="card-default">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold">Firewall Rules ({rules.length})</h3>
          <p className="text-sm text-muted-foreground">Network firewall rules and access policies</p>
        </div>
        <DataTable<FirewallRule>
          columns={columns}
          data={rules}
          enableSorting={false}
          enableFiltering={false}
          enablePagination={false}
          emptyMessage="No firewall rules found"
        />
      </div>
    </div>
  );
}