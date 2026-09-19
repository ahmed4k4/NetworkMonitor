"use client";

import React, { useState, useEffect, useCallback } from "react";
import { format, formatDistanceToNow } from "date-fns";
import { getToken } from "@/lib/api";

interface DatabaseStats {
  database_size: string;
  total_tables: number;
  total_rows: number;
  tables: TableInfo[];
  record_counts: Record<string, number>;
  timestamp: string;
}

interface TableInfo {
  name: string;
  size: string;
  size_bytes: number;
  estimated_rows: number;
  record_count: number;
}

interface BackupInfo {
  id: string;
  path: string;
  created_at: string;
  size_bytes: number;
  size_human: string;
  metadata: {
    type?: string;
    status?: string;
    [key: string]: unknown;
  };
  has_database: boolean;
  has_config: boolean;
}

interface BackupsResponse {
  backups: BackupInfo[];
}

const API_BASE = "/api";

const dataTypes = [
  { value: "flows", label: "Flows" },
  { value: "traffic_samples", label: "Traffic Samples" },
  { value: "dns_queries", label: "DNS Queries" },
  { value: "domains", label: "Domains" },
  { value: "applications", label: "Applications" },
  { value: "usage_daily", label: "Daily Usage" },
  { value: "usage_hourly", label: "Hourly Usage" },
  { value: "usage_monthly", label: "Monthly Usage" },
  { value: "alerts", label: "Alerts" },
  { value: "events", label: "Events" },
  { value: "audit_logs", label: "Audit Logs" },
  { value: "device_app_usage", label: "Device App Usage" },
  { value: "device_domain_usage", label: "Device Domain Usage" },
  { value: "device_category_usage", label: "Device Category Usage" },
  { value: "device_protocol_usage", label: "Device Protocol Usage" },
  { value: "device_peaks", label: "Device Peaks" },
  { value: "device_activity_timeline", label: "Device Activity Timeline" },
  { value: "sni_observations", label: "SNI Observations" },
];

const trafficTypes = [
  { value: "", label: "All" },
  { value: "download", label: "Download" },
  { value: "upload", label: "Upload" },
];

const formats = [
  { value: "csv", label: "CSV" },
  { value: "excel", label: "Excel (XLSX)" },
  { value: "pdf", label: "PDF" },
];

export function DataManagementContent() {
  const [stats, setStats] = useState<DatabaseStats | null>(null);
  const [backups, setBackups] = useState<BackupInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "export" | "delete" | "backups" | "restore">("overview");
  const [exportForm, setExportForm] = useState({
    format: "csv",
    data_type: "flows",
    device_id: "",
    start_date: "",
    end_date: "",
    traffic_type: "",
    domain: "",
    application: "",
    limit: 10000,
  });
  const [deleteForm, setDeleteForm] = useState({
    data_type: "flows",
    device_id: "",
    start_date: "",
    end_date: "",
    confirm: false,
    reason: "",
  });
  const [backupForm, setBackupForm] = useState({
    backup_type: "full",
    include_data: true,
    description: "",
  });
  const [restoreForm, setRestoreForm] = useState({
    backup_id: "",
    confirm: false,
    restore_data: true,
  });
  const [selectedBackup, setSelectedBackup] = useState<BackupInfo | null>(null);
  const [messages, setMessages] = useState<{ type: "success" | "error"; text: string }[]>([]);

  const fetchStats = useCallback(async () => {
    try {
      const token = getToken();
      const response = await fetch(`${API_BASE}/data-management/stats`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchBackups = useCallback(async () => {
    try {
      const token = getToken();
      const response = await fetch(`${API_BASE}/data-management/backups`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setBackups(data.backups || []);
      }
    } catch (error) {
      console.error("Failed to fetch backups:", error);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchStats();
    fetchBackups();
  }, []);

  const handleExport = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const token = getToken();
      const params = new URLSearchParams();
      Object.entries(exportForm).forEach(([key, value]) => {
        if (value !== "" && value !== null) {
          params.append(key, String(value));
        }
      });

      const response = await fetch(`${API_BASE}/data-management/export`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(exportForm),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        const disposition = response.headers.get("Content-Disposition");
        let filename = `export_${exportForm.data_type}_${format(new Date(), "yyyyMMdd_HHmmss")}`;
        if (disposition) {
          const match = disposition.match(/filename="?([^"]+)"?/);
          if (match) filename = match[1];
        }
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        addMessage("success", "Export completed successfully");
      } else {
        const error = await response.json();
        addMessage("error", error.detail || "Export failed");
      }
    } catch (error) {
      addMessage("error", "Export failed: " + (error as Error).message);
    }
  };

  const handleDelete = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!deleteForm.confirm) {
      addMessage("error", "Deletion requires explicit confirmation");
      return;
    }
    if (!deleteForm.reason.trim()) {
      addMessage("error", "Reason is required for audit trail");
      return;
    }

    try {
      const token = getToken();
      const response = await fetch(`${API_BASE}/data-management/delete`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(deleteForm),
      });

      if (response.ok) {
        const data = await response.json();
        addMessage("success", data.message || "Deletion completed");
        fetchStats();
      } else {
        const error = await response.json();
        addMessage("error", error.detail || "Deletion failed");
      }
    } catch (error) {
      addMessage("error", "Deletion failed: " + (error as Error).message);
    }
  };

  const handleBackup = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const token = getToken();
      const response = await fetch(`${API_BASE}/data-management/backup`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ ...backupForm, confirm: true }),
      });

      if (response.ok) {
        const data = await response.json();
        addMessage("success", data.message || "Backup started");
        fetchBackups();
      } else {
        const error = await response.json();
        addMessage("error", error.detail || "Backup failed");
      }
    } catch (error) {
      addMessage("error", "Backup failed: " + (error as Error).message);
    }
  };

  const handleRestore = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!restoreForm.confirm) {
      addMessage("error", "Restore requires explicit confirmation");
      return;
    }
    if (!restoreForm.backup_id) {
      addMessage("error", "Please select a backup to restore");
      return;
    }

    try {
      const token = getToken();
      const response = await fetch(`${API_BASE}/data-management/restore`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(restoreForm),
      });

      if (response.ok) {
        const data = await response.json();
        addMessage("success", data.message || "Restore started");
      } else {
        const error = await response.json();
        addMessage("error", error.detail || "Restore failed");
      }
    } catch (error) {
      addMessage("error", "Restore failed: " + (error as Error).message);
    }
  };

  const handleVerifyBackup = async (backupId: string) => {
    try {
      const token = getToken();
      const response = await fetch(`${API_BASE}/data-management/backups/${backupId}/verify`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      if (data.valid) {
        addMessage("success", `Backup ${backupId} verified successfully`);
      } else {
        addMessage("error", `Backup ${backupId} verification failed: ${JSON.stringify(data.checks)}`);
      }
    } catch (error) {
      addMessage("error", "Verification failed: " + (error as Error).message);
    }
  };

  const handleDeleteBackup = async (backupId: string) => {
    if (!window.confirm(`Are you sure you want to delete backup ${backupId}?`)) return;
    try {
      const token = getToken();
      const response = await fetch(`${API_BASE}/data-management/backups/${backupId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        addMessage("success", `Backup ${backupId} deleted`);
        fetchBackups();
      } else {
        const error = await response.json();
        addMessage("error", error.detail || "Failed to delete backup");
      }
    } catch (error) {
      addMessage("error", "Delete failed: " + (error as Error).message);
    }
  };

  const addMessage = (type: "success" | "error", text: string) => {
    setMessages((prev) => [...prev, { type, text }]);
    setTimeout(() => {
      setMessages((prev) => prev.slice(1));
    }, 5000);
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64">Loading...</div>;
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Messages */}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`px-4 py-3 rounded-lg shadow-lg text-white min-w-[300px] ${
              msg.type === "success" ? "bg-green-600" : "bg-red-600"
            }`}
          >
            {msg.text}
          </div>
        ))}
      </div>

      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Data Management Center</h1>
        <p className="text-gray-600 mt-1">Database statistics, export, deletion, backup, and restore operations</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8" aria-label="Data management tabs">
          {[
            { id: "overview", label: "Overview" },
            { id: "export", label: "Export Data" },
            { id: "delete", label: "Delete Data" },
            { id: "backups", label: "Backups" },
            { id: "restore", label: "Restore" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === "overview" && stats && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard title="Database Size" value={stats.database_size} icon="💾" />
            <StatCard title="Total Tables" value={stats.total_tables.toString()} icon="📋" />
            <StatCard title="Total Rows" value={stats.total_rows.toLocaleString()} icon="📊" />
            <StatCard title="Last Updated" value={formatDistanceToNow(new Date(stats.timestamp), { addSuffix: true })} icon="🕐" />
          </div>

          {/* Key Metrics */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Record Counts by Category</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Records</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {Object.entries(stats.record_counts)
                    .filter(([, count]) => count > 0)
                    .sort(([, a], [, b]) => b - a)
                    .map(([key, count]) => (
                      <tr key={key} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{key.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500 font-mono">{count.toLocaleString()}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Table Sizes */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Table Sizes</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Table</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Size</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Est. Rows</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actual Rows</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {stats.tables.map((table) => (
                    <tr key={table.name} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-mono">{table.name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500">{table.size}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500 font-mono">{table.estimated_rows.toLocaleString()}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500 font-mono">{table.record_count.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Export Tab */}
      {activeTab === "export" && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Export Data</h2>
          <p className="text-gray-600 mb-6">Export real database data in CSV, Excel, or PDF format with filtering options.</p>
          <form onSubmit={handleExport} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Format</label>
                <select
                  value={exportForm.format}
                  onChange={(e) => setExportForm({ ...exportForm, format: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {formats.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Data Type</label>
                <select
                  value={exportForm.data_type}
                  onChange={(e) => setExportForm({ ...exportForm, data_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {dataTypes.map((dt) => <option key={dt.value} value={dt.value}>{dt.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Device ID (optional)</label>
                <input
                  type="text"
                  value={exportForm.device_id}
                  onChange={(e) => setExportForm({ ...exportForm, device_id: e.target.value })}
                  placeholder="Enter device ID"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Limit</label>
                <input
                  type="number"
                  value={exportForm.limit}
                  onChange={(e) => setExportForm({ ...exportForm, limit: parseInt(e.target.value) || 10000 })}
                  min="1"
                  max="100000"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                <input
                  type="date"
                  value={exportForm.start_date}
                  onChange={(e) => setExportForm({ ...exportForm, start_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                <input
                  type="date"
                  value={exportForm.end_date}
                  onChange={(e) => setExportForm({ ...exportForm, end_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Traffic Type</label>
                <select
                  value={exportForm.traffic_type}
                  onChange={(e) => setExportForm({ ...exportForm, traffic_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {trafficTypes.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Domain Filter</label>
                <input
                  type="text"
                  value={exportForm.domain}
                  onChange={(e) => setExportForm({ ...exportForm, domain: e.target.value })}
                  placeholder="Filter by domain"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="pt-4 border-t border-gray-200">
              <button
                type="submit"
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Export Data
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Delete Tab */}
      {activeTab === "delete" && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <h3 className="text-lg font-semibold text-yellow-800 mb-2">⚠️ Destructive Operation</h3>
            <p className="text-yellow-700">Data deletion is permanent and cannot be undone. Always ensure you have a recent backup before proceeding.</p>
            <ul className="text-yellow-700 mt-2 space-y-1 list-disc list-inside">
              <li>Requires explicit confirmation checkbox</li>
              <li>Requires a reason for audit trail</li>
              <li>All deletions are logged in audit logs</li>
              <li>At least one filter (device, date range) is required</li>
            </ul>
          </div>

          <h2 className="text-xl font-semibold text-gray-900 mb-6">Delete Data</h2>
          <form onSubmit={handleDelete} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Data Type</label>
                <select
                  value={deleteForm.data_type}
                  onChange={(e) => setDeleteForm({ ...deleteForm, data_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {dataTypes.map((dt) => <option key={dt.value} value={dt.value}>{dt.label}</option>)}
                  <option value="all">All Data Types (with filters)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Device ID (optional)</label>
                <input
                  type="text"
                  value={deleteForm.device_id}
                  onChange={(e) => setDeleteForm({ ...deleteForm, device_id: e.target.value })}
                  placeholder="Enter device ID"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                <input
                  type="date"
                  value={deleteForm.start_date}
                  onChange={(e) => setDeleteForm({ ...deleteForm, start_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                <input
                  type="date"
                  value={deleteForm.end_date}
                  onChange={(e) => setDeleteForm({ ...deleteForm, end_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Reason (required)</label>
              <textarea
                value={deleteForm.reason}
                onChange={(e) => setDeleteForm({ ...deleteForm, reason: e.target.value })}
                rows={3}
                placeholder="Enter reason for deletion (required for audit log)"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={deleteForm.confirm}
                  onChange={(e) => setDeleteForm({ ...deleteForm, confirm: e.target.checked })}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">I confirm I want to permanently delete this data</span>
              </label>
            </div>

            <div className="pt-4 border-t border-gray-200">
              <button
                type="submit"
                disabled={!deleteForm.confirm || !deleteForm.reason.trim()}
                className="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Delete Data
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Backups Tab */}
      {activeTab === "backups" && (
        <div className="space-y-6">
          {/* Create Backup */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Create Backup</h2>
            <form onSubmit={handleBackup} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Backup Type</label>
                  <select
                    value={backupForm.backup_type}
                    onChange={(e) => setBackupForm({ ...backupForm, backup_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="full">Full (Database + Config + Rules + Settings)</option>
                    <option value="database">Database Only</option>
                    <option value="config">Configuration Only</option>
                    <option value="rules">Rules Only</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Include Data</label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={backupForm.include_data}
                      onChange={(e) => setBackupForm({ ...backupForm, include_data: e.target.checked })}
                      className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Include database dump</span>
                  </label>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description (optional)</label>
                  <input
                    type="text"
                    value={backupForm.description}
                    onChange={(e) => setBackupForm({ ...backupForm, description: e.target.value })}
                    placeholder="Backup description"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <button
                type="submit"
                className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
              >
                Create Backup
              </button>
            </form>
          </div>

          {/* Backups List */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Available Backups</h2>
            </div>
            {backups.length === 0 ? (
              <div className="p-8 text-center text-gray-500">No backups found</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Backup ID</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Size</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Components</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {backups.map((backup) => (
                      <tr key={backup.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">{backup.id}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatDistanceToNow(new Date(backup.created_at), { addSuffix: true })}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">{backup.metadata.type || "unknown"}</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{backup.size_human}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <span className={backup.has_database ? "text-green-600" : "text-red-600"}>
                            {backup.has_database ? "✓" : "✗"} DB
                          </span>
                          <span className="mx-2">{backup.has_config ? "✓ Config" : "✗ Config"}</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                            backup.metadata.status === "completed"
                              ? "bg-green-100 text-green-800"
                              : backup.metadata.status === "failed"
                              ? "bg-red-100 text-red-800"
                              : "bg-yellow-100 text-yellow-800"
                          }`}>
                            {backup.metadata.status || "unknown"}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                          <button
                            onClick={() => handleVerifyBackup(backup.id)}
                            className="text-blue-600 hover:text-blue-900 text-sm"
                          >
                            Verify
                          </button>
                          <button
                            onClick={() => setSelectedBackup(backup)}
                            className="text-green-600 hover:text-green-900 text-sm"
                          >
                            Restore
                          </button>
                          <button
                            onClick={() => handleDeleteBackup(backup.id)}
                            className="text-red-600 hover:text-red-900 text-sm"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Restore Tab */}
      {activeTab === "restore" && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <h3 className="text-lg font-semibold text-red-800 mb-2">⚠️ Dangerous Operation</h3>
            <p className="text-red-700">Restoring from backup will OVERWRITE current data. This cannot be undone. Ensure you have a current backup before proceeding.</p>
          </div>

          <h2 className="text-xl font-semibold text-gray-900 mb-6">Restore from Backup</h2>
          <form onSubmit={handleRestore} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Select Backup</label>
              <select
                value={restoreForm.backup_id}
                onChange={(e) => setRestoreForm({ ...restoreForm, backup_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select a backup...</option>
                {backups.map((backup) => (
                  <option key={backup.id} value={backup.id}>
                    {backup.id} ({backup.size_human}, {backup.metadata.status})
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={restoreForm.restore_data}
                    onChange={(e) => setRestoreForm({ ...restoreForm, restore_data: e.target.checked })}
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Restore database data</span>
                </label>
              </div>
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={restoreForm.confirm}
                    onChange={(e) => setRestoreForm({ ...restoreForm, confirm: e.target.checked })}
                    className="h-4 w-4 text-red-600 border-gray-300 rounded focus:ring-red-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">I understand this will overwrite current data</span>
                </label>
              </div>
            </div>

            <div className="pt-4 border-t border-gray-200">
              <button
                type="submit"
                disabled={!restoreForm.confirm || !restoreForm.backup_id}
                className="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Restore from Backup
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Restore Confirmation Modal */}
      {selectedBackup && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Confirm Restore</h3>
            <p className="text-gray-600 mb-4">Restore from backup <strong>{selectedBackup.id}</strong>?</p>
            <p className="text-sm text-gray-500 mb-4">Size: {selectedBackup.size_human} | Type: {selectedBackup.metadata.type}</p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setSelectedBackup(null)}
                className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setRestoreForm({ ...restoreForm, backup_id: selectedBackup.id });
                  setActiveTab("restore");
                  setSelectedBackup(null);
                }}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                Proceed to Restore
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ title, value, icon }: { title: string; value: string; icon: string }) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
        <div className="text-3xl">{icon}</div>
      </div>
    </div>
  );
}