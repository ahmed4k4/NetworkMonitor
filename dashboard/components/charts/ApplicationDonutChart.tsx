"use client";

import React from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { formatBytes, calculatePercentage, getCategoryColor, isEmptyData } from "./utils";
import { DonutChartProps } from "./types";

export default function ApplicationDonutChart({
  data,
  height = 320,
  className = "",
  loading = false,
  emptyMessage = "No application data available",
  innerRadius = 60,
  outerRadius = 100,
  showLegend = true,
  showLabels = true,
}: DonutChartProps) {
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

  const total = data.reduce((sum, d) => sum + (d.value || 0), 0);

  return (
    <div className={`h-[${height}px] w-full ${className}`}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={innerRadius}
            outerRadius={outerRadius}
            paddingAngle={2}
            dataKey="value"
            nameKey="name"
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            label={showLabels ? ({ name, value, percent }: any) => 
              `${name || ''} ${((percent || 0) * 100).toFixed(1)}%` : false}
            labelLine={showLabels}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color || getCategoryColor(entry.category || entry.name, index)} />
            ))}
          </Pie>

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
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            labelFormatter={(label: any) => label}
          />

          {showLegend && (
            <Legend
              layout="vertical"
              align="right"
              verticalAlign="middle"
              iconType="circle"
              iconSize={10}
              formatter={(value) => {
                const item = data.find(d => d.name === value);
                if (item) {
                  const pct = calculatePercentage(item.value, total);
                  const confidence = item.confidence ? ` [${item.confidence}]` : '';
                  return `${value}${confidence} (${pct}%)`;
                }
                return value;
              }}
            />
          )}
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}