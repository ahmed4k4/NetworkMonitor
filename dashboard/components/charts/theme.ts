/**
 * Chart Theme Configuration
 * Consistent theming across all charts for light/dark mode
 */

export const CHART_COLORS = {
  // Primary chart colors
  download: '#3b82f6',    // blue-500
  upload: '#22c55e',      // green-500
  total: '#8b5cf6',       // violet-500
  
  // Category colors for donut/bar charts
  categories: [
    '#3b82f6', // blue - streaming
    '#22c55e', // green - social
    '#f59e0b', // amber - gaming
    '#ef4444', // red - download
    '#8b5cf6', // violet - browsing
    '#ec4899', // pink - cloud
    '#06b6d4', // cyan - messaging
    '#f97316', // orange - other
  ],
  
  // Protocol colors
  protocols: {
    TCP: '#3b82f6',
    UDP: '#22c55e',
    ICMP: '#f59e0b',
    DNS: '#ef4444',
    HTTP: '#8b5cf6',
    HTTPS: '#ec4899',
    QUIC: '#06b6d4',
    TLS: '#f97316',
    SSH: '#64748b',
    OTHER: '#94a3b8',
  },
  
  // Severity colors
  severity: {
    CRITICAL: '#ef4444',
    WARNING: '#f59e0b',
    INFO: '#3b82f6',
  },
  
  // Neutral grays
  gray: {
    50: '#f8fafc',
    100: '#f1f5f9',
    200: '#e2e8f0',
    300: '#cbd5e1',
    400: '#94a3b8',
    500: '#64748b',
    600: '#475569',
    700: '#334155',
    800: '#1e293b',
    900: '#0f172a',
  },
};

export const CHART_THEME = {
  // Light theme
  light: {
    background: '#ffffff',
    surface: '#f8fafc',
    text: '#0f172a',
    textMuted: '#64748b',
    grid: '#e2e8f0',
    axis: '#94a3b8',
    tooltipBg: '#ffffff',
    tooltipBorder: '#e2e8f0',
    tooltipText: '#0f172a',
  },
  
  // Dark theme
  dark: {
    background: '#0f172a',
    surface: '#1e293b',
    text: '#f8fafc',
    textMuted: '#94a3b8',
    grid: '#334155',
    axis: '#64748b',
    tooltipBg: '#1e293b',
    tooltipBorder: '#334155',
    tooltipText: '#f8fafc',
  },
};

export const CHART_MARGIN = {
  top: 10,
  right: 30,
  left: 20,
  bottom: 10,
};

export const CHART_ANIMATION_DURATION = 500;

export const CHART_TOOLTIP_STYLE = {
  backgroundColor: 'var(--chart-tooltip-bg)',
  border: '1px solid var(--chart-tooltip-border)',
  borderRadius: '8px',
  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
  color: 'var(--chart-tooltip-text)',
  fontSize: '12px',
  padding: '8px 12px',
};