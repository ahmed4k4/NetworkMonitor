"use client";

import { useCallback, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { DataTable } from "@/components/design-system";
import { StatusBadge } from "@/components/design-system";
import { MetricCard } from "@/components/design-system";
import { Button } from "@/components/ui/button";
import { api, isAuthenticated } from "@/lib/api";
import { Report } from "@/lib/types";
import { RefreshCw, Download, FileText } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";

export default function ReportsPage() {
  const router = useRouter();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [reportType, setReportType] = useState("DAILY");
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  const loadReportsData = useCallback(async () => {
    try {
      const reportsData = await api.getReports();
      setReports(Array.isArray(reportsData) ? reportsData : []);
    } catch (err) {
      console.error("Failed to load reports data:", err);
      setError(err instanceof Error ? err.message : "Failed to load reports data");
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
      loadReportsData();
    }, 0);

    return () => clearTimeout(timer);
  }, [router, loadReportsData]);

  const handleGenerateReport = async () => {
    setGenerating(true);
    setError(null);

    try {
      await api.generateReport({ type: reportType });
      await loadReportsData();
    } catch (err) {
      console.error("Failed to generate report:", err);
      setError(err instanceof Error ? err.message : "Failed to generate report");
    } finally {
      setGenerating(false);
    }
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
    loadReportsData();
  };

  // Columns for DataTable
  const columns: ColumnDef<Report>[] = [
    {
      id: "name",
      header: "Report",
      cell: (info) => (
        <div>
          <div className="font-medium">{info.row.original.type} Report</div>
          <div className="text-sm text-muted-foreground">{info.row.original.id}</div>
        </div>
      ),
    },
    {
      id: "type",
      header: "Type",
      cell: (info) => (
        <StatusBadge variant="active" size="xs" label={info.row.original.type} />
      ),
    },
    {
      id: "period",
      header: "Period",
      cell: (info) => (
        <span>
          {formatDate(info.row.original.period_start)} — {formatDate(info.row.original.period_end)}
        </span>
      ),
    },
    {
      id: "status",
      header: "Status",
      cell: (info) => (
        <StatusBadge 
          variant={info.row.original.status === "COMPLETED" ? "success" : "pending"} 
          size="sm" 
          label={info.row.original.status || "PROCESSING"} 
        />
      ),
    },
    {
      id: "generated",
      header: "Generated",
      cell: (info) => formatDate(info.row.original.created_at),
    },
    {
      id: "actions",
      header: "Actions",
      cell: (info) => {
        const report = info.row.original;
        if (report.status === "COMPLETED" && report.file_url) {
          return (
            <a
              href={report.file_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 rounded-md border border-input bg-background px-3 py-1.5 text-sm font-medium hover:bg-accent hover:text-accent-foreground"
            >
              <Download className="h-4 w-4 mr-1" />
              Download
            </a>
          );
        }
        return <StatusBadge variant="pending" size="sm" label="Processing" />;
      },
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading reports data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-red-500">Unable to load reports</h2>
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
          <h1 className="text-3xl font-bold">Network Reports</h1>
          <p className="text-muted-foreground">Generate and download network traffic and usage reports</p>
        </div>
        <button onClick={handleRefresh} disabled={loading} className="px-3 py-1.5 text-sm bg-primary text-white rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-2">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Report Generator */}
      <div className="card-default">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Generate Report
          </h3>
          <p className="text-sm text-muted-foreground">Create a new network report</p>
        </div>
        <div className="p-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <select 
              value={reportType} 
              onChange={(e) => setReportType(e.target.value)}
              className="w-[200px] px-3 py-1.5 text-sm bg-background border border-border rounded-md"
            >
              <option value="DAILY">Daily Report</option>
              <option value="WEEKLY">Weekly Report</option>
              <option value="MONTHLY">Monthly Report</option>
              <option value="CUSTOM">Custom Report</option>
            </select>
            <Button onClick={handleGenerateReport} disabled={generating}>
              {generating ? "Generating..." : "Generate Report"}
            </Button>
          </div>
        </div>
      </div>

      {/* Reports Table - Using new DataTable from design system */}
      <div className="card-default">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold">Generated Reports ({reports.length})</h3>
          <p className="text-sm text-muted-foreground">Previously generated network reports</p>
        </div>
        <DataTable<Report>
          columns={columns}
          data={reports}
          enableSorting={false}
          enableFiltering={false}
          enablePagination={false}
          emptyMessage="No reports found"
        />
      </div>
    </div>
  );
}