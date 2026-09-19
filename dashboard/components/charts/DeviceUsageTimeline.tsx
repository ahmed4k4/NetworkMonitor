"use client";

import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { formatBytes, formatTooltipTime, formatTime, isEmptyData } from "./utils";
import { CHART_THEME, CHART_MARGIN, CHART_COLORS } from "./theme";
import { ChartDataPoint } from "./types";

interface DeviceUsageTimelineProps {
  data: ChartDataPoint[];
  height?: number;
  className?: string;
  loading?: boolean;
  emptyMessage?: string;
  timeRange?: string;
}

export default function DeviceUsageTimeline({
  data,
  height = 280,
  className = "",
  loading = false,
  emptyMessage = "No usage history available",
  timeRange = "7d",
}: DeviceUsageTimelineProps) {
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

  const sortedData = [...data].sort(
    (a, b) => new Date(a.time).getTime() - new Date(b.time).getTime()
  );

  return (
    <div className={`h-[${height}px] w-full ${className}`}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={sortedData} margin={CHART_MARGIN}>
          <defs>
            <linearGradient id="downloadTimelineGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={CHART_COLORS.download} stopOpacity={0.3} />
              <stop offset="95%" stopColor={CHART_COLORS.download} stopOpacity={0} />
            </linearGradient>
            <linearGradient id="uploadTimelineGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={CHART_COLORS.upload} stopOpacity={0.3} />
              <stop offset="95%" stopColor={CHART_COLORS.upload} stopOpacity={0} />
            </linearGradient>
          </defs>

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
              name === 'download' || name === 'upload' ? formatBytes(value) : value,
              name.charAt(0).toUpperCase() + name.slice(1),
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

          <Area
            type="monotone"
            dataKey="download"
            name="Download"
            stroke={CHART_COLORS.download}
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#downloadTimelineGradient)"
            connectNulls={true}
          />

          <Area
            type="monotone"
            dataKey="upload"
            name="Upload"
            stroke={CHART_COLORS.upload}
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#uploadTimelineGradient)"
            connectNulls={true}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}