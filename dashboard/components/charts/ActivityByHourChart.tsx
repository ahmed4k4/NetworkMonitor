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
} from "recharts";
import { formatBytes, isEmptyData } from "./utils";
import { CHART_COLORS } from "./theme";
import { BarDataPoint } from "./types";

interface ActivityByHourChartProps {
  data: BarDataPoint[];
  height?: number;
  className?: string;
  loading?: boolean;
  emptyMessage?: string;
}

export default function ActivityByHourChart({
  data,
  height = 280,
  className = "",
  loading = false,
  emptyMessage = "No activity data available",
}: ActivityByHourChartProps) {
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

  // Sort by hour
  const sortedData = [...data].sort((a, b) => {
    const hourA = parseInt(a.name.split(':')[0] || '0', 10);
    const hourB = parseInt(b.name.split(':')[0] || '0', 10);
    return hourA - hourB;
  });

  return (
    <div className={`h-[${height}px] w-full ${className}`}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={sortedData}
          layout="horizontal"
          margin={{ top: 10, right: 10, left: 60, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" vertical={true} />

          <XAxis
            type="number"
            tickFormatter={(value) => formatBytes(value)}
            tick={{ fill: '#64748b', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />

          <YAxis
            type="category"
            dataKey="name"
            width={50}
            tick={{ fill: '#64748b', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />

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

          <Bar
            dataKey="value"
            name="Activity"
            radius={[4, 0, 0, 4]}
            maxBarSize={25}
          >
            {sortedData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={
                  entry.extra?.active === false
                    ? CHART_COLORS.gray[300]
                    : CHART_COLORS.download
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}