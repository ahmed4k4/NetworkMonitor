"use client";

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Legend,
} from "recharts";
import { formatBytes, isEmptyData, getCategoryColor } from "./utils";
import { BarDataPoint } from "./types";

interface ProtocolBarChartProps {
  data: BarDataPoint[];
  height?: number;
  className?: string;
  loading?: boolean;
  emptyMessage?: string;
  horizontal?: boolean;
}

export default function ProtocolBarChart({
  data,
  height = 320,
  className = "",
  loading = false,
  emptyMessage = "No protocol data available",
  horizontal = true,
}: ProtocolBarChartProps) {
  if (loading) {
    return (
      <div className={`h-[${height}px] w-full animate-pulse bg-muted/50 rounded-lg ${className}`} />
    );
  }

  if (isEmptyData(data)) {
    return (
      <div className={`h-[${height}px] w-full flex items-center justify-center text-muted-foreground ${className}`}>
        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className={`h-[${height}px] w-full ${className}`}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout={horizontal ? "vertical" : "horizontal"}
          margin={{ top: 10, right: 30, left: horizontal ? 80 : 20, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" vertical={!horizontal} />

          {horizontal ? (
            <>
              <XAxis
                type="number"
                tickFormatter={(value) => formatBytes(value)}
                tick={{ fill: '#64748b', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                type="category"
                dataKey="name"
                width={80}
                tick={{ fill: '#64748b', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
            </>
          ) : (
            <>
              <XAxis
                dataKey="name"
                tick={{ fill: '#64748b', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tickFormatter={(value) => formatBytes(value)}
                tick={{ fill: '#64748b', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
            </>
          )}

          <Tooltip
            contentStyle={{
              backgroundColor: '#ffffff',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            }}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter={(value: any, name: any) => [
              formatBytes(value),
              name,
            ]}
          />

          <Legend wrapperStyle={{ paddingTop: 10 }} />

          <Bar
            dataKey="value"
            name="Traffic"
            radius={[0, 4, 4, 0]}
            maxBarSize={35}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color || getCategoryColor(entry.name, index)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}