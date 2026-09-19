"use client";

import { cn } from "@/lib/utils";
import {
  ColumnDef,
  flexRender,
  createColumnHelper,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  useReactTable,
  SortingState,
  ColumnFiltersState,
  PaginationState,
  Table,
} from "@tanstack/react-table";
import {
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  Search,
  Loader2,
  Check,
} from "lucide-react";
import { useState, ReactNode, useCallback, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";

interface DataTableProps<TData> {
  /** Column definitions */
  columns: ColumnDef<TData, unknown>[];
  /** Data to display */
  data: TData[];
  /** Whether data is loading */
  loading?: boolean;
  /** Empty state message */
  emptyMessage?: string;
  /** Enable sorting */
  enableSorting?: boolean;
  /** Enable filtering */
  enableFiltering?: boolean;
  /** Enable pagination */
  enablePagination?: boolean;
  /** Page size options */
  pageSizeOptions?: number[];
  /** Default page size */
  defaultPageSize?: number;
  /** Row click handler */
  onRowClick?: (row: TData) => void;
  /** Custom row key */
  getRowId?: (row: TData) => string;
  /** Additional CSS classes */
  className?: string;
  /** Toolbar content (actions, filters, etc.) */
  toolbar?: ReactNode;
  /** Show row numbers */
  showRowNumbers?: boolean;
  /** Striped rows */
  striped?: boolean;
  /** Hoverable rows */
  hoverable?: boolean;
  /** Custom empty state */
  emptyState?: ReactNode;
  /** Enable row selection */
  enableSelection?: boolean;
  /** Selection model (controlled) */
  selectedRows?: Set<string>;
  /** Selection change handler */
  onSelectionChange?: (selected: Set<string>) => void;
}

function DataTableHeader<TData>({
  table,
  header,
}: {
  table: Table<TData>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  header: any;
}) {
  const column = header.column;
  const canSort = column.getCanSort();
  const isSorted = column.getIsSorted();
  const toggleSorting = column.getToggleSortingHandler();
  const columnSize = column.getSize();

  return (
    <th
      className={cn(
        "text-table-header p-3 text-left align-top border-b border-border-strong bg-surface",
        "select-none",
        canSort && "cursor-pointer hover:bg-hover transition-colors",
        columnSize && columnSize < 100 && "whitespace-nowrap"
      )}
      onClick={toggleSorting}
      style={columnSize ? { width: `${columnSize}px` } : undefined}
      scope="col"
    >
      <div className="flex items-center gap-2">
        {flexRender(column.columnDef.header, header.getContext())}
        {canSort && (
          <span className="flex items-center">
            {isSorted === "asc" ? (
              <ChevronUp className="h-4 w-4 text-text-secondary" />
            ) : isSorted === "desc" ? (
              <ChevronDown className="h-4 w-4 text-text-secondary" />
            ) : (
              <ChevronDown className="h-4 w-4 text-text-muted/50" />
            )}
          </span>
        )}
      </div>
    </th>
  );
}

function DataTableToolbar<TData>({
  table,
  toolbar,
  enableFiltering,
  pageSizeOptions = [10, 25, 50, 100],
}: {
  table: Table<TData>;
  toolbar?: ReactNode;
  enableFiltering?: boolean;
  pageSizeOptions?: number[];
}) {
  const globalFilter = table.getState().globalFilter ?? "";

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 border-b border-border">
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 w-full sm:w-auto">
        {toolbar}
        {enableFiltering && (
          <div className="relative w-full sm:w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
            <Input
              type="search"
              placeholder="Search..."
              value={globalFilter as string}
              onChange={(e) => table.setGlobalFilter(e.target.value)}
              className="pl-9 pr-3 py-1.5 text-sm bg-background border-border"
              aria-label="Filter table"
            />
          </div>
        )}
      </div>

      {table.getPageCount() > 1 && (
        <div className="flex items-center gap-2">
          <select
            value={table.getState().pagination.pageSize}
            onChange={(e) => table.setPageSize(Number(e.target.value))}
            className="px-2 py-1 text-sm bg-background border border-border rounded-md"
            aria-label="Rows per page"
          >
            {pageSizeOptions.map((size) => (
              <option key={size} value={size}>
                {size} per page
              </option>
            ))}
          </select>

          <div className="flex items-center gap-1 text-sm text-text-secondary">
            Page{" "}
            <input
              type="number"
              min={1}
              max={table.getPageCount()}
              value={table.getState().pagination.pageIndex + 1}
              onChange={(e) => table.setPageIndex(Number(e.target.value) - 1)}
              className="w-16 px-2 py-1 text-center bg-background border border-border rounded-md"
              aria-label="Page number"
            />
            of {table.getPageCount()}
          </div>

          <Button
            variant="ghost"
            size="icon"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            aria-label="Previous page"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            aria-label="Next page"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}

function DataTablePagination<TData>({
  table,
  pageSizeOptions = [10, 25, 50, 100],
}: {
  table: Table<TData>;
  pageSizeOptions?: number[];
}) {
  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-2 p-4 border-t border-border">
      <div className="flex items-center gap-2">
        <span className="text-sm text-text-secondary">
          Showing{" "}
          <span className="font-mono">
            {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1}
          </span>{" "}
          to{" "}
          <span className="font-mono">
            {Math.min(
              (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
              table.getFilteredRowModel().rows.length
            )}
          </span>{" "}
          of{" "}
          <span className="font-mono">{table.getFilteredRowModel().rows.length}</span>{" "}
          results
        </span>
        <select
          value={table.getState().pagination.pageSize}
          onChange={(e) => table.setPageSize(Number(e.target.value))}
          className="px-2 py-1 text-sm bg-background border border-border rounded-md"
          aria-label="Rows per page"
        >
          {pageSizeOptions.map((size) => (
            <option key={size} value={size}>
              {size} per page
            </option>
          ))}
        </select>
      </div>

      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage()}
          aria-label="Previous page"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage()}
          aria-label="Next page"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

export function DataTable<TData>({
  columns,
  data,
  loading = false,
  emptyMessage = "No data available",
  enableSorting = true,
  enableFiltering = true,
  enablePagination = true,
  pageSizeOptions = [10, 25, 50, 100],
  defaultPageSize = 25,
  onRowClick,
  getRowId,
  className,
  toolbar,
  showRowNumbers = false,
  striped = true,
  hoverable = true,
  emptyState,
  enableSelection = false,
  selectedRows = new Set(),
  onSelectionChange,
}: DataTableProps<TData>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = useState("");
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: defaultPageSize,
  });
  
  // Keyboard navigation state
  const [focusedRowIndex, setFocusedRowIndex] = useState<number>(-1);
  const rowRefs = useRef<Map<string, HTMLTableRowElement>>(new Map());
  
  // Store the table reference for keyboard navigation
  const tableRef = useRef<Table<TData> | null>(null);

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      columnFilters,
      globalFilter,
      pagination,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    onPaginationChange: setPagination,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: enableSorting ? getSortedRowModel() : undefined,
    getFilteredRowModel: enableFiltering ? getFilteredRowModel() : undefined,
    getPaginationRowModel: enablePagination ? getPaginationRowModel() : undefined,
    getRowId,
    debugTable: false,
  });

  // Store table reference for keyboard handlers
  useEffect(() => {
    tableRef.current = table;
  }, [table]);

  // Handle keyboard navigation for rows
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (!enableSelection && !onRowClick) return;
    
    const rows = table.getRowModel().rows;
    if (rows.length === 0) return;

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setFocusedRowIndex(prev => Math.min(prev + 1, rows.length - 1));
        break;
      case "ArrowUp":
        e.preventDefault();
        setFocusedRowIndex(prev => Math.max(prev - 1, 0));
        break;
      case "Home":
        e.preventDefault();
        setFocusedRowIndex(0);
        break;
      case "End":
        e.preventDefault();
        setFocusedRowIndex(rows.length - 1);
        break;
      case "Enter":
      case " ":
        if (focusedRowIndex >= 0 && onRowClick) {
          e.preventDefault();
          onRowClick(rows[focusedRowIndex].original);
        }
        break;
      case "Escape":
        if (focusedRowIndex >= 0) {
          setFocusedRowIndex(-1);
        }
        break;
      default:
        break;
    }
  }, [table, onRowClick, enableSelection, focusedRowIndex]);

  // Focus the row element when focusedRowIndex changes
  useEffect(() => {
    if (focusedRowIndex >= 0) {
      const rows = table.getRowModel().rows;
      if (focusedRowIndex < rows.length) {
        const row = rows[focusedRowIndex];
        const rowEl = rowRefs.current.get(row.id);
        rowEl?.focus();
      }
    }
  }, [focusedRowIndex, table]);

  // Handle selection
  const isRowSelected = (rowId: string) => selectedRows.has(rowId);
  
  const handleRowSelection = (rowId: string, selected: boolean) => {
    if (!onSelectionChange) return;
    
    const newSelection = new Set(selectedRows);
    if (selected) {
      newSelection.add(rowId);
    } else {
      newSelection.delete(rowId);
    }
    onSelectionChange(newSelection);
  };

  const handleSelectAll = (selected: boolean) => {
    if (!onSelectionChange) return;
    
    const rows = table.getFilteredRowModel().rows;
    const newSelection = new Set(selectedRows);
    
    if (selected) {
      rows.forEach(row => newSelection.add(row.id));
    } else {
      rows.forEach(row => newSelection.delete(row.id));
    }
    onSelectionChange(newSelection);
  };

  const allRowsSelected = table.getFilteredRowModel().rows.length > 0 &&
    table.getFilteredRowModel().rows.every(row => selectedRows.has(row.id));
  const someRowsSelected = table.getFilteredRowModel().rows.some(row => selectedRows.has(row.id)) &&
    !allRowsSelected;

  if (loading) {
    return (
      <div className={cn("card-default", className)}>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
          <span className="sr-only">Loading table data...</span>
        </div>
      </div>
    );
  }

  const hasFilteredData = table.getFilteredRowModel().rows.length > 0;

  return (
    <div className={cn("card-default overflow-hidden", className)}>
      {(toolbar || enableFiltering) && (
        <DataTableToolbar
          table={table}
          toolbar={toolbar}
          enableFiltering={enableFiltering}
          pageSizeOptions={pageSizeOptions}
        />
      )}

      <div className="overflow-x-auto" onKeyDown={handleKeyDown} tabIndex={0}>
        <table className="w-full" role="grid">
          <thead className="sticky top-0 z-10">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {enableSelection && (
                  <th className="text-table-header p-3 text-left border-b border-border-strong bg-surface w-12">
                    <Checkbox
                      checked={allRowsSelected}
                      indeterminate={someRowsSelected}
                      onCheckedChange={handleSelectAll}
                      aria-label="Select all rows"
                    />
                  </th>
                )}
                {showRowNumbers && !enableSelection && (
                  <th className="text-table-header p-3 text-left border-b border-border-strong bg-surface w-12" />
                )}
                {headerGroup.headers.map((header) => (
                  <DataTableHeader 
                    key={header.id} 
                    table={table} 
                    header={header} 
                  />
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-border">
            {hasFilteredData ? (
              table.getRowModel().rows.map((row, rowIndex: number) => {
                const rowId = row.id;
                const selected = isRowSelected(rowId);
                const isFocused = rowIndex === focusedRowIndex;
                
                return (
                  <tr
                    key={rowId}
                    ref={(el) => {
                      if (el) {
                        rowRefs.current.set(rowId, el);
                      } else {
                        rowRefs.current.delete(rowId);
                      }
                    }}
                    className={cn(
                      "transition-colors",
                      hoverable && "hover:bg-hover",
                      striped && rowIndex % 2 === 1 && "bg-hover/50",
                      selected && "bg-primary-50 dark:bg-primary-900/20",
                      isFocused && "ring-2 ring-primary-500 ring-inset",
                      onRowClick && "cursor-pointer"
                    )}
                    onClick={() => onRowClick?.(row.original)}
                    onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onRowClick?.(row.original)}
                    tabIndex={onRowClick || enableSelection ? 0 : -1}
                    role={onRowClick ? "button" : "row"}
                    aria-selected={selected}
                    onFocus={() => setFocusedRowIndex(rowIndex)}
                    onBlur={() => setFocusedRowIndex(-1)}
                  >
                    {enableSelection && (
                      <td className="p-3 text-table-cell text-text-muted">
                        <Checkbox
                          checked={selected}
                          onCheckedChange={(checked: boolean) => handleRowSelection(rowId, checked)}
                          aria-label={`Select row ${rowIndex + 1}`}
                        />
                      </td>
                    )}
                    {showRowNumbers && !enableSelection && (
                      <td className="p-3 text-table-cell text-text-muted font-mono">
                        {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + rowIndex + 1}
                      </td>
                    )}
                    {row.getVisibleCells().map((cell) => (
                      <td
                        key={cell.id}
                        className={cn(
                          "p-3 text-table-cell align-top",
                          cell.column.getSize() && cell.column.getSize()! < 100 && "whitespace-nowrap"
                        )}
                        style={cell.column.getSize() ? { width: `${cell.column.getSize()}px` } : undefined}
                      >
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                );
              })
            ) : (
              <tr>
                <td
                  colSpan={columns.length + (showRowNumbers || enableSelection ? 1 : 0)}
                  className="px-6 py-12 text-center"
                >
                  {emptyState || (
                    <div className="flex flex-col items-center gap-3 text-text-muted">
                      <Loader2 className="h-10 w-10 text-border-strong" />
                      <p className="text-body-sm">{emptyMessage}</p>
                    </div>
                  )}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {enablePagination && table.getPageCount() > 1 && (
        <DataTablePagination table={table} pageSizeOptions={pageSizeOptions} />
      )}
    </div>
  );
}

export default DataTable;
export type { DataTableProps };
