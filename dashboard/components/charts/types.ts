/**
 * Chart Types
 * Shared TypeScript types for chart components
 */

export interface ChartDataPoint {
  time: string;
  download: number;
  upload: number;
  total?: number;
  [key: string]: string | number | undefined;
}

export interface TooltipPayload {
  value: number;
  name: string;
  color: string;
  payload: ChartDataPoint;
}

export interface DonutDataPoint {
  name: string;
  value: number;
  color?: string;
  category?: string;
  confidence?: string;
  connections?: number;
}

export interface BarDataPoint {
  name: string;
  value: number;
  secondaryValue?: number;
  color?: string;
  extra?: Record<string, unknown>;
}

export interface TimeRangeOption {
  value: string;
  label: string;
  hours: number;
}

export const TIME_RANGES: TimeRangeOption[] = [
  { value: '1h', label: '1 Hour', hours: 1 },
  { value: '5m', label: '5 Minutes', hours: 5/60 },
  { value: '15m', label: '15 Minutes', hours: 15/60 },
  { value: '1h', label: '1 Hour', hours: 1 },
  { value: '24h', label: '24 Hours', hours: 24 },
  { value: '7d', label: '7 Days', hours: 168 },
  { value: '30d', label: '30 Days', hours: 720 },
];

export interface ChartProps {
  data: ChartDataPoint[] | DonutDataPoint[] | BarDataPoint[];
  height?: number;
  width?: string | number;
  className?: string;
  loading?: boolean;
  emptyMessage?: string;
}

export interface TrafficChartProps extends ChartProps {
  data: ChartDataPoint[];
  timeRange?: string;
  showTotal?: boolean;
}

export interface DonutChartProps extends ChartProps {
  data: DonutDataPoint[];
  innerRadius?: number;
  outerRadius?: number;
  showLegend?: boolean;
  showLabels?: boolean;
}

export interface BarChartProps extends ChartProps {
  data: BarDataPoint[];
  horizontal?: boolean;
  showValues?: boolean;
  maxBars?: number;
  xKey?: string;
  yKey?: string;
}