/**
 * Chart Components Library
 * 
 * Unified charting library for Network Monitor dashboard.
 * Uses Recharts with consistent theming, tooltips, and formatting.
 * All charts use real backend data - no mock/random values.
 */

// Dashboard Charts
export { default as TrafficChart } from './TrafficChart';
export { default as CategoryDonutChart } from './CategoryDonutChart';
export { default as TopConsumersBarChart } from './TopConsumersBarChart';

// Device Details Charts
export { default as DeviceUsageTimeline } from './DeviceUsageTimeline';
export { default as ApplicationDonutChart } from './ApplicationDonutChart';
export { default as TopDomainsBarChart } from './TopDomainsBarChart';
export { default as SpeedSparkline } from './SpeedSparkline';
export { default as ActivityByHourChart } from './ActivityByHourChart';

// Analytics Charts
export { default as MultiDeviceComparisonChart } from './MultiDeviceComparisonChart';
export { default as ProtocolBarChart } from './ProtocolBarChart';
export { default as HistoricalTrendChart } from './HistoricalTrendChart';
export { default as CategoryTrendChart } from './CategoryTrendChart';

// Re-export utilities
export { formatBytes, formatSpeed, formatTime } from './utils';
export { CHART_COLORS, CHART_THEME, CHART_MARGIN } from './theme';
export type { ChartDataPoint, BarDataPoint, DonutDataPoint } from './types';
