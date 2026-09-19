"use client";

import { useCallback, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { DataTable } from "@/components/design-system";
import { api, isAuthenticated } from "@/lib/api";
import { DomainStat } from "@/lib/types";
import { RefreshCw, Search, Globe } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";

export default function DomainsPage() {
  const router = useRouter();
  const [domains, setDomains] = useState<DomainStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState("queries");
  const [error, setError] = useState<string | null>(null);

  const loadDomainsData = useCallback(async () => {
    try {
      const domainsData = await api.getDomainAnalytics();
      setDomains(Array.isArray(domainsData) ? domainsData : []);
    } catch (err) {
      console.error("Failed to load domains data:", err);
      setError(err instanceof Error ? err.message : "Failed to load domains data");
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
      loadDomainsData();
    }, 0);

    return () => clearTimeout(timer);
  }, [router, loadDomainsData]);

  // Sort domains
  const sortedDomains = [...domains].sort((a, b) => {
    switch (sortBy) {
      case "queries":
        return b.queries - a.queries;
      case "devices":
        return b.devices - a.devices;
      case "name":
        return a.domain.localeCompare(b.domain);
      case "time":
      default:
        return new Date(b.last_seen).getTime() - new Date(a.last_seen).getTime();
    }
  });

  // Filter domains
  const filteredDomains = sortedDomains.filter((domain) => {
    if (searchTerm && !domain.domain.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }
    return true;
  });

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

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
    loadDomainsData();
  };

  // Columns for DataTable
  const columns: ColumnDef<DomainStat>[] = [
    {
      id: "domain",
      header: "Domain",
      cell: (info) => (
        <div className="flex items-center gap-2">
          <Globe className="h-4 w-4 text-blue-500" />
          <span className="font-medium">{info.row.original.domain}</span>
        </div>
      ),
    },
    {
      id: "queries",
      header: "Queries",
      cell: (info) => <div className="text-right">{info.row.original.queries}</div>,
    },
    {
      id: "devices",
      header: "Devices",
      cell: (info) => <div className="text-right">{info.row.original.devices}</div>,
    },
    {
      id: "traffic",
      header: "Traffic",
      cell: (info) => (
        <div className="text-right">{formatBytes(info.row.original.traffic)}</div>
      ),
    },
    {
      id: "last_seen",
      header: "Last Seen",
      cell: (info) => formatDate(info.row.original.last_seen),
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading domains data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-red-500">Unable to load domains</h2>
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
          <h1 className="text-3xl font-bold">Domain Analysis</h1>
          <p className="text-muted-foreground">Monitor domain access and network traffic</p>
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
                placeholder="Search domains..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8 w-full px-3 py-1.5 text-sm bg-background border border-border rounded-md"
              />
            </div>
            <select 
              value={sortBy} 
              onChange={(e) => setSortBy(e.target.value)}
              className="w-[180px] px-3 py-1.5 text-sm bg-background border border-border rounded-md"
            >
              <option value="queries">Query Count</option>
              <option value="devices">Device Count</option>
              <option value="name">Domain Name</option>
              <option value="time">Last Seen</option>
            </select>
          </div>
        </div>
      </div>

      {/* Domains Table - Using new DataTable from design system */}
      <div className="card-default">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold">Top Domains ({filteredDomains.length})</h3>
          <p className="text-sm text-muted-foreground">Most frequently accessed domains and their network traffic</p>
        </div>
        <DataTable<DomainStat>
          columns={columns}
          data={filteredDomains}
          enableSorting={false}
          enableFiltering={false}
          enablePagination={false}
          emptyMessage="No domains found"
        />
      </div>
    </div>
  );
}