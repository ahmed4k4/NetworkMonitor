"use client";

import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface StatusBadgeProps {
  /** Status variant */
  variant: "online" | "offline" | "warning" | "danger" | "unknown" | "active" | "inactive" | "pending" | "success";
  /** Optional custom label (overrides default) */
  label?: string;
  /** Size variant */
  size?: "xs" | "sm" | "md";
  /** Whether to show a pulse animation for active states */
  pulse?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** Whether to show as dot only (no text) */
  dotOnly?: boolean;
  /** Tooltip text */
  title?: string;
}

const variantConfig = {
  online: {
    defaultLabel: "Online",
    bg: "bg-success-100 text-success-700 dark:bg-success-900/30 dark:text-success-400",
    dot: "bg-success-500",
    pulseColor: "bg-success-500",
  },
  offline: {
    defaultLabel: "Offline",
    bg: "bg-muted text-text-muted",
    dot: "bg-text-muted",
    pulseColor: "bg-text-muted",
  },
  warning: {
    defaultLabel: "Warning",
    bg: "bg-warning-100 text-warning-700 dark:bg-warning-900/30 dark:text-warning-400",
    dot: "bg-warning-500",
    pulseColor: "bg-warning-500",
  },
  danger: {
    defaultLabel: "Error",
    bg: "bg-danger-100 text-danger-700 dark:bg-danger-900/30 dark:text-danger-400",
    dot: "bg-danger-500",
    pulseColor: "bg-danger-500",
  },
  unknown: {
    defaultLabel: "Unknown",
    bg: "bg-muted text-text-muted",
    dot: "bg-text-muted",
    pulseColor: "bg-text-muted",
  },
  active: {
    defaultLabel: "Active",
    bg: "bg-success-100 text-success-700 dark:bg-success-900/30 dark:text-success-400",
    dot: "bg-success-500",
    pulseColor: "bg-success-500",
  },
  inactive: {
    defaultLabel: "Inactive",
    bg: "bg-muted text-text-muted",
    dot: "bg-text-muted",
    pulseColor: "bg-text-muted",
  },
  pending: {
    defaultLabel: "Pending",
    bg: "bg-warning-100 text-warning-700 dark:bg-warning-900/30 dark:text-warning-400",
    dot: "bg-warning-500",
    pulseColor: "bg-warning-500",
  },
  success: {
    defaultLabel: "Success",
    bg: "bg-success-100 text-success-700 dark:bg-success-900/30 dark:text-success-400",
    dot: "bg-success-500",
    pulseColor: "bg-success-500",
  },
} as const;

const sizeStyles = {
  xs: {
    badge: "px-1.5 py-0.5 text-[10px]",
    dot: "h-1.5 w-1.5",
    gap: "gap-1",
  },
  sm: {
    badge: "px-2 py-0.5 text-xs",
    dot: "h-2 w-2",
    gap: "gap-1.5",
  },
  md: {
    badge: "px-2.5 py-1 text-sm",
    dot: "h-2.5 w-2.5",
    gap: "gap-2",
  },
};

// Keyframes for smooth transitions
const transitionStyles = "transition-all duration-300 ease-in-out";

export function StatusBadge({
  variant,
  label,
  size = "sm",
  pulse = false,
  className,
  dotOnly = false,
  title,
}: StatusBadgeProps) {
  const config = variantConfig[variant];
  const sizes = sizeStyles[size];
  const displayLabel = label ?? config.defaultLabel;

  // Enhanced pulse animation with smoother timing
  const pulseAnimation = pulse && (variant === "online" || variant === "active" || variant === "success") ? (
    <span
      className={cn(
        "absolute inset-0 rounded-full animate-ping opacity-75",
        config.pulseColor,
        "duration-2000 ease-in-out"
      )}
      aria-hidden="true"
    />
  ) : null;

  if (dotOnly) {
    return (
      <span
        className={cn(
          "inline-flex items-center",
          sizes.gap,
          className,
          transitionStyles
        )}
        title={title ?? displayLabel}
      >
        <span className="relative flex-shrink-0">
          <span
            className={cn(
              "rounded-full",
              sizes.dot,
              config.dot,
              transitionStyles
            )}
          />
          {pulseAnimation}
        </span>
        {!dotOnly && <span className={cn("font-medium", sizes.badge, transitionStyles)}>{displayLabel}</span>}
      </span>
    );
  }

  return (
    <span
      className={cn(
        "inline-flex items-center font-medium rounded-full border",
        sizes.badge,
        config.bg,
        "border-transparent",
        className,
        transitionStyles
      )}
      title={title}
    >
      <span className="relative flex-shrink-0">
        <span
          className={cn(
            "rounded-full",
            sizes.dot,
            config.dot,
            transitionStyles
          )}
        />
        {pulseAnimation}
      </span>
      <span className={cn("truncate", transitionStyles)}>{displayLabel}</span>
    </span>
  );
}

interface StatusIndicatorProps {
  /** Status variant */
  variant: StatusBadgeProps["variant"];
  /** Size of the indicator dot */
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  /** Whether to show pulse animation */
  pulse?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** Tooltip/aria-label */
  label?: string;
}

/**
 * Standalone status indicator dot (without text label)
 */
export function StatusIndicator({
  variant,
  size = "md",
  pulse = false,
  className,
  label,
}: StatusIndicatorProps) {
  const config = variantConfig[variant];
  
  const sizeMap = {
    xs: "h-1.5 w-1.5",
    sm: "h-2 w-2",
    md: "h-2.5 w-2.5",
    lg: "h-3 w-3",
    xl: "h-4 w-4",
  };

  // Enhanced pulse animation with smoother timing
  const pulseAnimation = pulse && (variant === "online" || variant === "active" || variant === "success") ? (
    <span
      className={cn(
        "absolute inset-0 rounded-full animate-ping opacity-75",
        config.pulseColor,
        "duration-2000 ease-in-out"
      )}
      aria-hidden="true"
    />
  ) : null;

  return (
    <span
      className={cn(
        "relative inline-flex",
        className,
        transitionStyles
      )}
      aria-label={label ?? config.defaultLabel}
      role="status"
    >
      <span
        className={cn(
          "rounded-full",
          sizeMap[size],
          config.dot,
          transitionStyles
        )}
      />
      {pulseAnimation}
    </span>
  );
}

export default StatusBadge;
export type { StatusBadgeProps, StatusIndicatorProps };
