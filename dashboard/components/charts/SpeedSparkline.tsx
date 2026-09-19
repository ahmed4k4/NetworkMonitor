"use client";

import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { formatSpeed, formatTooltipTime, isEmptyData } from "./utils";
import { CHART_COLORS } from "./theme";
import { ChartDataPoint } from "./types";

interface SpeedSparklineProps {
  data: ChartDataPoint[];
  height?: number;
  className?: string;
  loading?: boolean;
  emptyMessage?: string;
  showLabels?: boolean;
}

export default function SpeedSparkline({
  data,
  height = 60,
  className = "",
  loading = false,
  emptyMessage = "No speed data",
  showLabels = false,
}: SpeedSparklineProps) {
  if (loading) {
    return (
      <div className={`h-[${height}px] w-full animate-pulse bg-muted/50 rounded ${className}`} />
    );
  }

  if (isEmptyData(data)) {
    return (
      <div className={`h-[${height}px] w-full flex items-center justify-center text-muted-foreground text-xs ${className}`}>
        <span>{emptyMessage}</span>
      </div>
    );
  }

  const sortedData = [...data]
    .sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime())
    .slice(-30); // Last 30 points for sparkline

  return (
    <div className={`h-[${height}px] w-full ${className}`}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={sortedData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
          {showLabels && (
            <XAxis
              dataKey="time"
              tickFormatter={(value) => new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              tick={{ fill: '#94a3b8', fontSize: 9 }}
              axisLine={false}
              tickLine={false}
            />
          )}
          <YAxis
            tickFormatter={(value) => formatSpeed(value)}
            tick={showLabels ? { fill: '#94a3b8', fontSize: 9 } : false}
            axisLine={false}
            tickLine={false}
            width={showLabels ? 40 : 0}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '6px',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
              color: '#f8fafc',
              fontSize: '11px',
            }}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter={(value: any, name: any) => [
              name === 'download' || name === 'upload' ? formatSpeed(value) : value,
              name.charAt(0).toUpperCase() + name.slice(1),
            ]}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            labelFormatter={(label: any, payload: any) => {
              if (Array.isArray(payload) && payload.length > 0 && payload[0]?.payload?.time) {
                return formatTooltipTime(payload[0].payload.time as string);
              }
              return typeof label === 'string' ? label : '';
            }}
          />
          <Line
            type="monotone"
            dataKey="download"
            stroke={CHART_COLORS.download}
            strokeWidth={1.5}
            dot={false}
            activeDot={showLabels ? { r: 3 } : false}
          />
          <Line
            type="monotone"
            dataKey="upload"
            stroke={CHART_COLORS.upload}
            strokeWidth={1.5}
            dot={false}
            activeDot={showLabels ? { r: 3 } : false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}