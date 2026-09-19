"use client";

import { useCallback, useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { DataTable } from "@/components/design-system";
import { StatusBadge } from "@/components/design-system";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { api, isAuthenticated } from "@/lib/api";
import { ControlRule, Device } from "@/lib/types";
import {
  RefreshCw,
  Plus,
  Filter,
  Play,
  Pause,
  Trash2,
  Pencil,
  Copy,
  Search,
} from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";

const EMPTY_FORM: ControlRule = {
  name: "",
  description: "",
  action: "ALLOW",
  enabled: true,
  device_id: "",
  rule_type: "DOMAIN",
  domain: "",
  schedule: "",
  priority: 0,
};

export default function RulesPage() {
  const router = useRouter();
  const [rules, setRules] = useState<ControlRule[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<ControlRule>({ ...EMPTY_FORM });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const loadRulesData = useCallback(async () => {
    try {
      const rulesData = await api.getRules();
      setRules(Array.isArray(rulesData) ? rulesData : []);
    } catch (err) {
      console.error("Failed to load rules data:", err);
      setError(err instanceof Error ? err.message : "Failed to load rules data");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadDevices = useCallback(async () => {
    try {
      const devs = await api.getDevices();
      setDevices(Array.isArray(devs) ? devs : []);
    } catch (err) {
      console.error("Failed to load devices:", err);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }
    const t = setTimeout(() => {
      loadRulesData();
      loadDevices();
    }, 0);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const deviceById = useMemo(() => {
    const map: Record<string, Device> = {};
    for (const d of devices) map[d.device_id] = d;
    return map;
  }, [devices]);

  const filteredRules = rules.filter((rule) => {
    if (statusFilter === "enabled" && !rule.enabled) return false;
    if (statusFilter === "disabled" && rule.enabled) return false;
    if (typeFilter !== "all" && (rule.rule_type || "DOMAIN") !== typeFilter) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      const hay = [
        rule.name,
        rule.description,
        rule.domain,
        rule.action,
        rule.rule_type,
        rule.device_id,
        rule.device_name,
        rule.device_ip,
        rule.schedule,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });

  const openCreate = () => {
    setEditingId(null);
    setForm({ ...EMPTY_FORM });
    setFormError(null);
    setDialogOpen(true);
  };

  const openEdit = (rule: ControlRule) => {
    setEditingId(rule.id ?? null);
    setForm({
      name: rule.name,
      description: rule.description ?? "",
      action: rule.action ?? "ALLOW",
      enabled: rule.enabled,
      device_id: rule.device_id ?? "",
      rule_type: rule.rule_type ?? "DOMAIN",
      domain: rule.domain ?? "",
      schedule: rule.schedule ?? "",
      priority: rule.priority ?? 0,
    });
    setFormError(null);
    setDialogOpen(true);
  };

  const openDuplicate = (rule: ControlRule) => {
    setEditingId(null);
    setForm({
      name: `${rule.name} (copy)`,
      description: rule.description ?? "",
      action: rule.action ?? "ALLOW",
      enabled: rule.enabled,
      device_id: rule.device_id ?? "",
      rule_type: rule.rule_type ?? "DOMAIN",
      domain: rule.domain ?? "",
      schedule: rule.schedule ?? "",
      priority: rule.priority ?? 0,
    });
    setFormError(null);
    setDialogOpen(true);
  };

  const set = (patch: Partial<ControlRule>) => setForm((f) => ({ ...f, ...patch }));

  const handleSave = async () => {
    if (!form.name.trim()) {
      setFormError("Rule name is required.");
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      const payload: ControlRule = {
        ...form,
        name: form.name.trim(),
        priority: Number(form.priority ?? 0),
      };
      if (editingId) {
        await api.updateRule(editingId, payload);
      } else {
        await api.createRule(payload);
      }
      setDialogOpen(false);
      await loadRulesData();
    } catch (err) {
      console.error("Failed to save rule:", err);
      setFormError(err instanceof Error ? err.message : "Failed to save rule");
    } finally {
      setSaving(false);
    }
  };

  const handleToggleRule = async (rule: ControlRule) => {
    if (!rule.id) return;
    try {
      await api.updateRule(rule.id, { ...rule, enabled: !rule.enabled });
      await loadRulesData();
    } catch (err) {
      console.error("Failed to toggle rule:", err);
      setError(err instanceof Error ? err.message : "Failed to toggle rule");
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!confirm("Are you sure you want to delete this rule?")) return;
    try {
      await api.deleteRule(ruleId);
      await loadRulesData();
    } catch (err) {
      console.error("Failed to delete rule:", err);
      setError(err instanceof Error ? err.message : "Failed to delete rule");
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return "—";
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  const columns: ColumnDef<ControlRule>[] = [
    {
      id: "name",
      header: "Name",
      cell: (info) => <div className="font-medium">{info.row.original.name}</div>,
    },
    {
      id: "device",
      header: "Device",
      cell: (info) => {
        const r = info.row.original;
        const name = r.device_name || deviceById[r.device_id || ""]?.custom_name || deviceById[r.device_id || ""]?.hostname || "—";
        const ip = r.device_ip || deviceById[r.device_id || ""]?.ip || "";
        return (
          <div className="text-sm">
            <div className="font-medium">{name}</div>
            {ip && <div className="text-xs text-muted-foreground">{ip}</div>}
          </div>
        );
      },
    },
    {
      id: "rule_type",
      header: "Type",
      cell: (info) => (
        <StatusBadge variant="active" size="xs" label={info.row.original.rule_type || "DOMAIN"} />
      ),
    },
    {
      id: "domain",
      header: "Domain / Pattern",
      cell: (info) => (
        <div className="text-sm font-mono">{info.row.original.domain || "—"}</div>
      ),
    },
    {
      id: "action",
      header: "Action",
      cell: (info) => {
        const a = info.row.original.action || "ALLOW";
        return (
          <StatusBadge
            variant={a === "BLOCK" || a === "DROP" ? "danger" : "active"}
            size="xs"
            label={a}
          />
        );
      },
    },
    {
      id: "schedule",
      header: "Schedule",
      cell: (info) => (
        <div className="text-sm text-muted-foreground">{info.row.original.schedule || "—"}</div>
      ),
    },
    {
      id: "priority",
      header: "Priority",
      cell: (info) => <div className="text-sm">{info.row.original.priority ?? 0}</div>,
    },
    {
      id: "status",
      header: "Status",
      cell: (info) => (
        <StatusBadge
          variant={info.row.original.enabled ? "active" : "inactive"}
          size="sm"
          label={info.row.original.enabled ? "Enabled" : "Disabled"}
        />
      ),
    },
    {
      id: "updated",
      header: "Updated",
      cell: (info) => {
        const ts = info.row.original.updated_at || info.row.original.created_at;
        return <div className="text-sm text-muted-foreground">{formatDate(ts)}</div>;
      },
    },
    {
      id: "actions",
      header: "Actions",
      cell: (info) => {
        const rule = info.row.original;
        return (
          <div className="flex items-center gap-1">
            <Button
              size="sm"
              variant="outline"
              title={rule.enabled ? "Disable" : "Enable"}
              onClick={() => handleToggleRule(rule)}
            >
              {rule.enabled ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            </Button>
            <Button size="sm" variant="outline" title="Edit" onClick={() => openEdit(rule)}>
              <Pencil className="h-4 w-4" />
            </Button>
            <Button size="sm" variant="outline" title="Duplicate" onClick={() => openDuplicate(rule)}>
              <Copy className="h-4 w-4" />
            </Button>
            {rule.id && (
              <Button
                size="sm"
                variant="destructive"
                title="Delete"
                onClick={() => handleDeleteRule(rule.id!)}
              >
                <Trash2 className="h-4 w-4" />
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
          <p className="mt-4 text-muted-foreground">Loading rules data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-red-500">Unable to load rules</h2>
        <p className="text-muted-foreground mt-2">{error}</p>
        <Button
          onClick={() => {
            setError(null);
            setLoading(true);
            loadRulesData();
          }}
          className="mt-4"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Network Rules</h1>
          <p className="text-muted-foreground">Manage network access policies and device controls</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={() => {
              setLoading(true);
              setError(null);
              loadRulesData();
            }}
            disabled={loading}
            size="sm"
            variant="outline"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button size="sm" onClick={openCreate}>
            <Plus className="h-4 w-4 mr-2" />
            Add Rule
          </Button>
        </div>
      </div>

      <div className="card-default">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </h3>
        </div>
        <div className="p-6 flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search name, domain, device, IP..."
              className="w-full pl-8 px-3 py-1.5 text-sm bg-background border border-border rounded-md"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-[160px] px-3 py-1.5 text-sm bg-background border border-border rounded-md"
          >
            <option value="all">All Status</option>
            <option value="enabled">Enabled</option>
            <option value="disabled">Disabled</option>
          </select>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="w-[160px] px-3 py-1.5 text-sm bg-background border border-border rounded-md"
          >
            <option value="all">All Types</option>
            <option value="DOMAIN">Domain</option>
            <option value="IP">IP</option>
            <option value="APP">Application</option>
            <option value="PROTOCOL">Protocol</option>
            <option value="SCHEDULE">Schedule</option>
          </select>
        </div>
      </div>

      <div className="card-default">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold">Network Rules ({filteredRules.length})</h3>
          <p className="text-sm text-muted-foreground">
            Active and scheduled network rules and policies
          </p>
        </div>
        <DataTable<ControlRule>
          columns={columns}
          data={filteredRules}
          enableSorting={false}
          enableFiltering={false}
          enablePagination={false}
          emptyMessage="No rules found"
        />
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingId ? "Edit Rule" : "Add Rule"}</DialogTitle>
            <DialogDescription>
              Configure a network access policy. Changes are enforced by the backend engine.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            <div>
              <label className="text-sm font-medium">Name *</label>
              <input
                value={form.name}
                onChange={(e) => set({ name: e.target.value })}
                placeholder="e.g. Block YouTube"
                className="mt-1 w-full px-3 py-1.5 text-sm bg-background border border-border rounded-md"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Description</label>
              <input
                value={form.description ?? ""}
                onChange={(e) => set({ description: e.target.value })}
                placeholder="Optional description"
                className="mt-1 w-full px-3 py-1.5 text-sm bg-background border border-border rounded-md"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Rule Type</label>
                <select
                  value={form.rule_type ?? "DOMAIN"}
                  onChange={(e) => set({ rule_type: e.target.value })}
                  className="mt-1 w-full px-3 py-1.5 text-sm bg-background border border-border rounded-md"
                >
                  <option value="DOMAIN">Domain</option>
                  <option value="IP">IP</option>
                  <option value="APP">Application</option>
                  <option value="PROTOCOL">Protocol</option>
                  <option value="SCHEDULE">Schedule</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">Action</label>
                <select
                  value={form.action ?? "ALLOW"}
                  onChange={(e) => set({ action: e.target.value })}
                  className="mt-1 w-full px-3 py-1.5 text-sm bg-background border border-border rounded-md"
                >
                  <option value="ALLOW">ALLOW</option>
                  <option value="BLOCK">BLOCK</option>
                  <option value="DROP">DROP</option>
                  <option value="THROTTLE">THROTTLE</option>
                </select>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium">Domain / Pattern</label>
              <input
                value={form.domain ?? ""}
                onChange={(e) => set({ domain: e.target.value })}
                placeholder={form.rule_type === "IP" ? "e.g. 192.168.1.0/24" : "e.g. youtube.com"}
                className="mt-1 w-full px-3 py-1.5 text-sm bg-background border border-border rounded-md"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Device</label>
              <select
                value={form.device_id ?? ""}
                onChange={(e) => set({ device_id: e.target.value })}
                className="mt-1 w-full px-3 py-1.5 text-sm bg-background border border-border rounded-md"
              >
                <option value="">All devices</option>
                {devices.map((d) => (
                  <option key={d.device_id} value={d.device_id}>
                    {d.custom_name || d.hostname || d.ip} ({d.ip})
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Schedule</label>
                <input
                  value={form.schedule ?? ""}
                  onChange={(e) => set({ schedule: e.target.value })}
                  placeholder="e.g. weekdays 09:00-17:00"
                  className="mt-1 w-full px-3 py-1.5 text-sm bg-background border border-border rounded-md"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Priority</label>
                <input
                  type="number"
                  value={form.priority ?? 0}
                  onChange={(e) => set({ priority: Number(e.target.value) })}
                  className="mt-1 w-full px-3 py-1.5 text-sm bg-background border border-border rounded-md"
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <input
                id="rule-enabled"
                type="checkbox"
                checked={form.enabled}
                onChange={(e) => set({ enabled: e.target.checked })}
                className="h-4 w-4"
              />
              <label htmlFor="rule-enabled" className="text-sm font-medium">
                Enabled
              </label>
            </div>

            {formError && (
              <p className="text-sm text-red-500">{formError}</p>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)} disabled={saving}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? "Saving..." : editingId ? "Update Rule" : "Create Rule"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}