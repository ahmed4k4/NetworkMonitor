"use client";

import { useCallback, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { DataTable } from "@/components/design-system";
import { StatusBadge } from "@/components/design-system";
import { api, isAuthenticated } from "@/lib/api";
import { Application } from "@/lib/types";
import { RefreshCw, Search } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";

const CATEGORIES = [
  "Streaming",
  "Social Media",
  "Gaming",
  "Cloud",
  "Communication",
  "Education",
  "Shopping",
  "Downloads",
  "Other",
];

export default function ApplicationsPage() {
  const router = useRouter();
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [error, setError] = useState<string | null>(null);

  const loadApplicationsData = useCallback(async () => {
    try {
      const appsData = await api.getApplicationAnalytics();
      setApplications(Array.isArray(appsData) ? appsData : []);
    } catch (err) {
      console.error("Failed to load applications data:", err);
      setError(err instanceof Error ? err.message : "Failed to load applications data");
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
      loadApplicationsData();
    }, 0);

    return () => clearTimeout(timer);
  }, [router, loadApplicationsData]);

  // Filter applications
  const filteredApplications = applications.filter((app) => {
    if (searchTerm && !app.name.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }

    if (categoryFilter !== "all" && app.category !== categoryFilter) {
      return false;
    }

    return true;
  });

  const totalTraffic = applications.reduce(
    (sum, app) => sum + Number(app.traffic || 0),
    0,
  );

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
    loadApplicationsData();
  };

  // Columns for DataTable
  const columns: ColumnDef<Application>[] = [
    {
      id: "application",
      header: "Application",
      cell: (info) => (
        <div className="font-medium">{info.row.original.name}</div>
      ),
    },
    {
      id: "category",
      header: "Category",
      cell: (info) => (
        <StatusBadge variant="active" size="xs" label={info.row.original.category || "Other"} />
      ),
    },
    {
      id: "traffic",
      header: "Traffic",
      cell: (info) => (
        <div className="text-right">{formatBytes(Number(info.row.original.traffic || 0))}</div>
      ),
    },
    {
      id: "devices",
      header: "Devices",
      cell: (info) => <div className="text-right">{Number(info.row.original.devices || 0)}</div>,
    },
    {
      id: "connections",
      header: "Connections",
      cell: (info) => <div className="text-right">{Number(info.row.original.connections || 0)}</div>,
    },
    {
      id: "percentage",
      header: "Percentage",
      cell: (info) => (
        <div className="text-right">
          {totalTraffic > 0
            ? ((Number(info.row.original.traffic || 0) / totalTraffic) * 100).toFixed(1)
            : "0.0"}%
        </div>
      ),
    },
    {
      id: "last_seen",
      header: "Last Seen",
      cell: (info) => info.row.original.last_seen ? formatDate(info.row.original.last_seen) : "—",
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading applications data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-red-500">Unable to load applications</h2>
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
          <h1 className="text-3xl font-bold">Application Usage</h1>
          <p className="text-muted-foreground">Monitor network applications and their usage patterns</p>
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
                placeholder="Search applications..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8 w-full px-3 py-1.5 text-sm bg-background border border-border rounded-md"
              />
            </div>
            <select 
              value={categoryFilter} 
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="w-[180px] px-3 py-1.5 text-sm bg-background border border-border rounded-md"
            >
              <option value="all">All Categories</option>
              {CATEGORIES.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Applications Table - Using new DataTable from design system */}
      <div className="card-default">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold">Applications ({filteredApplications.length})</h3>
          <p className="text-sm text-muted-foreground">Network applications detected by the engine</p>
        </div>
        <DataTable<Application>
          columns={columns}
          data={filteredApplications
            .slice()
            .sort((a, b) => Number(b.traffic || 0) - Number(a.traffic || 0))}
          enableSorting={false}
          enableFiltering={false}
          enablePagination={false}
          emptyMessage="No applications found"
        />
      </div>
    </div>
  );
}