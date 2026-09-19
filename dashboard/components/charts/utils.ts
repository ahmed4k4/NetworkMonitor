/**
 * Chart Utilities
 * Formatting and helper functions for charts
 */

import { CHART_COLORS } from './theme';

/**
 * Format bytes to human readable string
 */
export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  if (!isFinite(bytes) || bytes < 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const value = bytes / Math.pow(k, i);
  
  // Show 2 decimal places for MB/GB/TB, 1 for KB, 0 for Bytes
  const decimals = i >= 2 ? 2 : i === 1 ? 1 : 0;
  return `${value.toFixed(decimals)} ${sizes[i]}`;
}

/**
 * Format bits per second to human readable string
 */
export function formatSpeed(bps: number): string {
  if (!isFinite(bps) || bps < 0) return '0 bps';
  if (bps === 0) return '0 bps';
  
  if (bps >= 1_000_000_000) {
    return `${(bps / 1_000_000_000).toFixed(2)} Gbps`;
  }
  if (bps >= 1_000_000) {
    return `${(bps / 1_000_000).toFixed(2)} Mbps`;
  }
  if (bps >= 1_000) {
    return `${(bps / 1_000).toFixed(1)} Kbps`;
  }
  return `${bps.toFixed(0)} bps`;
}

/**
 * Format speed for display (MB/s or KB/s)
 */
export function formatSpeedBytes(bytesPerSec: number): string {
  if (!isFinite(bytesPerSec) || bytesPerSec < 0) return '0 B/s';
  if (bytesPerSec === 0) return '0 B/s';
  
  if (bytesPerSec >= 1_000_000) {
    return `${(bytesPerSec / 1_000_000).toFixed(2)} MB/s`;
  }
  if (bytesPerSec >= 1_000) {
    return `${(bytesPerSec / 1_000).toFixed(1)} KB/s`;
  }
  return `${bytesPerSec.toFixed(0)} B/s`;
}

/**
 * Format time for axis labels
 */
export function formatTime(dateString: string, timeRange?: string): string {
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    
    // For short time ranges, show time only
    if (timeRange === '1h' || timeRange === '5m' || timeRange === '15m') {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // For daily ranges, show date and time
    if (timeRange === '24h') {
      return date.toLocaleString([], { 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    }
    
    // For weekly+, show date
    return date.toLocaleDateString([], { 
      month: 'short', 
      day: 'numeric' 
    });
  } catch {
    return dateString;
  }
}

/**
 * Format tooltip time with full precision
 */
export function formatTooltipTime(dateString: string): string {
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    return date.toLocaleString();
  } catch {
    return dateString;
  }
}

/**
 * Get color for category
 */
export function getCategoryColor(category: string, index?: number): string {
  const normalized = category.toLowerCase();
  
  // Known categories
  const categoryMap: Record<string, string> = {
    'streaming': CHART_COLORS.categories[0],
    'social': CHART_COLORS.categories[1],
    'gaming': CHART_COLORS.categories[2],
    'download': CHART_COLORS.categories[3],
    'browsing': CHART_COLORS.categories[4],
    'cloud': CHART_COLORS.categories[5],
    'messaging': CHART_COLORS.categories[6],
    'other': CHART_COLORS.categories[7],
  };
  
  if (categoryMap[normalized]) return categoryMap[normalized];
  if (index !== undefined) return CHART_COLORS.categories[index % CHART_COLORS.categories.length];
  return CHART_COLORS.categories[7];
}

/**
 * Get color for protocol
 */
export function getProtocolColor(protocol: string): string {
  const normalized = protocol.toUpperCase();
  return CHART_COLORS.protocols[normalized as keyof typeof CHART_COLORS.protocols] || CHART_COLORS.protocols.OTHER;
}

/**
 * Get color for severity
 */
export function getSeverityColor(severity: string): string {
  const normalized = severity.toUpperCase();
  return CHART_COLORS.severity[normalized as keyof typeof CHART_COLORS.severity] || CHART_COLORS.severity.INFO;
}

/**
 * Calculate percentage
 */
export function calculatePercentage(value: number, total: number): number {
  if (!total || total === 0) return 0;
  return Math.round((value / total) * 1000) / 10; // 1 decimal place
}

/**
 * Sort data by value descending
 */
export function sortByValueDesc<T extends { value: number }>(data: T[]): T[] {
  return [...data].sort((a, b) => b.value - a.value);
}

/**
 * Limit data to top N items
 */
export function limitData<T>(data: T[], max: number): T[] {
  return data.slice(0, max);
}

/**
 * Aggregate small slices into "Other" for donut charts
 */
export function aggregateDonutData(
  data: Array<{ name: string; value: number; [key: string]: unknown }>,
  maxItems: number = 7
): Array<{ name: string; value: number; [key: string]: unknown }> {
  if (data.length <= maxItems) return data;
  
  const sorted = [...data].sort((a, b) => b.value - a.value);
  const top = sorted.slice(0, maxItems - 1);
  const otherValue = sorted.slice(maxItems - 1).reduce((sum, d) => sum + d.value, 0);
  
  return [
    ...top,
    { name: 'Other', value: otherValue, color: CHART_COLORS.gray[400] },
  ];
}

/**
 * Empty state check
 */
export function isEmptyData(data: unknown[]): boolean {
  return !data || data.length === 0 || data.every(d => {
    if (typeof d === 'object' && d !== null) {
      return Object.values(d).every(v => v === 0 || v === '');
    }
    return d === 0 || d === '';
  });
}

/**
 * Generate gradient id for chart areas
 */
export function generateGradientId(prefix: string): string {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
}