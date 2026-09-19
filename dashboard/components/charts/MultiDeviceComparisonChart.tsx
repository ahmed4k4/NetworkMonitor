"use client";

import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { formatBytes, formatTooltipTime, formatTime, isEmptyData, getCategoryColor } from "./utils";
import { CHART_THEME, CHART_MARGIN } from "./theme";
import { ChartDataPoint } from "./types";

interface MultiDeviceComparisonChartProps {
  data: ChartDataPoint[];
  devices: string[];
  height?: number;
  className?: string;
  loading?: boolean;
  emptyMessage?: string;
  timeRange?: string;
  metric?: 'download' | 'upload' | 'total';
}

export default function MultiDeviceComparisonChart({
  data,
  devices,
  height = 320,
  className = "",
  loading = false,
  emptyMessage = "No comparison data available",
  timeRange = "1h",
  metric = 'total',
}: MultiDeviceComparisonChartProps) {
  if (loading) {
    return (
      <div className={`h-[${height}px] w-full animate-pulse bg-muted/50 rounded-lg ${className}`} />
    );
  }

  if (isEmptyData(data) || devices.length === 0) {
    return (
      <div className={`h-[${height}px] w-full flex items-center justify-center text-muted-foreground ${className}`}>
        <p>{emptyMessage}</p>
      </div>
    );
  }

  const sortedData = [...data].sort(
    (a, b) => new Date(a.time).getTime() - new Date(b.time).getTime()
  );

  // Generate colors for each device
  const deviceColors = devices.reduce((acc, device, index) => {
    acc[device] = getCategoryColor(device, index);
    return acc;
  }, {} as Record<string, string>);

  return (
    <div className={`h-[${height}px] w-full ${className}`}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={sortedData} margin={CHART_MARGIN}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_THEME.light.grid} vertical={false} />

          <XAxis
            dataKey="time"
            tickFormatter={(value) => formatTime(value, timeRange)}
            tick={{ fill: CHART_THEME.light.axis, fontSize: 10 }}
            axisLine={{ stroke: CHART_THEME.light.axis }}
            tickLine={false}
            dy={5}
          />

          <YAxis
            tickFormatter={(value) => formatBytes(value)}
            tick={{ fill: CHART_THEME.light.axis, fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            dx={-10}
            width={50}
          />

          <Tooltip
            contentStyle={{
              backgroundColor: CHART_THEME.light.tooltipBg,
              border: `1px solid ${CHART_THEME.light.tooltipBorder}`,
              borderRadius: '8px',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            }}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter={(value: any, name: any) => [
              formatBytes(value),
              name,
            ]}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            labelFormatter={(label: any, payload: any) => {
              if (Array.isArray(payload) && payload.length > 0 && payload[0]?.payload?.time) {
                return formatTooltipTime(payload[0].payload.time as string);
              }
              return typeof label === 'string' ? label : '';
            }}
            labelStyle={{ color: CHART_THEME.light.tooltipText, fontWeight: 500 }}
          />

          <Legend wrapperStyle={{ paddingTop: 10 }} />

          {devices.map((device, index) => (
            <Line
              key={device}
              type="monotone"
              dataKey={`${device}_${metric}`}
              name={device}
              stroke={deviceColors[device]}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
              connectNulls={true}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}