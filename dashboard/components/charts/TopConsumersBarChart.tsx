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
import { formatBytes, formatSpeed, isEmptyData, getCategoryColor } from "./utils";
import { BarChartProps } from "./types";

export default function TopConsumersBarChart({
  data,
  height = 320,
  className = "",
  loading = false,
  emptyMessage = "No device data available",
  horizontal = true,
  showValues = true,
  maxBars = 10,
}: BarChartProps) {
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

  const limitedData = data.slice(0, maxBars);
  const xKey = "name";
  const yKey = "value";

  return (
    <div className={`h-[${height}px] w-full ${className}`}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={limitedData}
          layout={horizontal ? "vertical" : "horizontal"}
          margin={{ top: 10, right: 30, left: horizontal ? 120 : 20, bottom: 10 }}
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
                dataKey={xKey}
                width={120}
                tick={{ fill: '#64748b', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
            </>
          ) : (
            <>
              <XAxis
                dataKey={xKey}
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

          <Legend />

          <Bar
            dataKey={yKey}
            name="Usage"
            radius={[0, 4, 4, 0]}
            maxBarSize={40}
          >
            {limitedData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color || getCategoryColor(entry.name, index)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}