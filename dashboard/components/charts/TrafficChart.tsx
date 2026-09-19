"use client";

import React from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from "recharts";
import { formatSpeed, formatTooltipTime, formatTime, isEmptyData } from "./utils";
import { CHART_THEME, CHART_MARGIN, CHART_COLORS } from "./theme";
import { TrafficChartProps } from "./types";

interface TooltipPayloadItem {
  payload?: {
    time?: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export default function TrafficChart({
  data,
  height = 320,
  className = "",
  loading = false,
  emptyMessage = "No traffic data available",
  timeRange = "1h",
  showTotal = false,
}: TrafficChartProps) {
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

  // Sort data by time
  const sortedData = [...data].sort(
    (a, b) => new Date(a.time).getTime() - new Date(b.time).getTime()
  );

  // Calculate total if needed
  const chartData = showTotal
    ? sortedData.map((d) => ({
        ...d,
        total: (d.download || 0) + (d.upload || 0),
      }))
    : sortedData;

  return (
    <div className={`h-[${height}px] w-full ${className}`}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={chartData}
          margin={CHART_MARGIN}
        >
          <defs>
            <linearGradient id="downloadGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={CHART_COLORS.download} stopOpacity={0.3} />
              <stop offset="95%" stopColor={CHART_COLORS.download} stopOpacity={0} />
            </linearGradient>
            <linearGradient id="uploadGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={CHART_COLORS.upload} stopOpacity={0.3} />
              <stop offset="95%" stopColor={CHART_COLORS.upload} stopOpacity={0} />
            </linearGradient>
            {showTotal && (
              <linearGradient id="totalGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={CHART_COLORS.total} stopOpacity={0.2} />
                <stop offset="95%" stopColor={CHART_COLORS.total} stopOpacity={0} />
              </linearGradient>
            )}
          </defs>

          <CartesianGrid
            strokeDasharray="3 3"
            stroke={CHART_THEME.light.grid}
            vertical={false}
          />

          <XAxis
            dataKey="time"
            tickFormatter={(value) => formatTime(value, timeRange)}
            tick={{ fill: CHART_THEME.light.axis, fontSize: 11 }}
            axisLine={{ stroke: CHART_THEME.light.axis }}
            tickLine={false}
            dy={5}
          />

          <YAxis
            tickFormatter={(value) => formatSpeed(value)}
            tick={{ fill: CHART_THEME.light.axis, fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            dx={-10}
            width={60}
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
              name === 'download' || name === 'upload' || name === 'total'
                ? value !== undefined && value !== null ? formatSpeed(value) : '-'
                : value,
              name?.charAt(0).toUpperCase() + name?.slice(1) || '',
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

          <Legend
            wrapperStyle={{ paddingTop: 10 }}
            formatter={(value) => value.charAt(0).toUpperCase() + value.slice(1)}
          />

          <Area
            type="monotone"
            dataKey="download"
            name="Download"
            stroke={CHART_COLORS.download}
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#downloadGradient)"
            connectNulls={true}
          />

          <Area
            type="monotone"
            dataKey="upload"
            name="Upload"
            stroke={CHART_COLORS.upload}
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#uploadGradient)"
            connectNulls={true}
          />

          {showTotal && (
            <Area
              type="monotone"
              dataKey="total"
              name="Total"
              stroke={CHART_COLORS.total}
              strokeWidth={1.5}
              strokeDasharray="5 5"
              fillOpacity={1}
              fill="url(#totalGradient)"
              connectNulls={true}
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}