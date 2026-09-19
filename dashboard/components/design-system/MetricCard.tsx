"use client";

import { cn } from "@/lib/utils";
import { ReactNode, forwardRef, useEffect, useRef, useState } from "react";

interface MetricCardProps {
  /** The main metric value to display */
  value: string | number;
  /** Label describing the metric */
  label: string;
  /** Optional icon to display */
  icon?: ReactNode;
  /** Trend indicator (positive, negative, neutral) */
  trend?: "up" | "down" | "neutral";
  /** Trend value (e.g., "+12%") */
  trendValue?: string;
  /** Color variant for the metric */
  variant?: "primary" | "success" | "warning" | "danger" | "info" | "neutral";
  /** Size variant */
  size?: "sm" | "md" | "lg";
  /** Additional CSS classes */
  className?: string;
  /** Click handler */
  onClick?: () => void;
  /** Whether the card is in a loading state */
  loading?: boolean;
  /** Duration for number animation in ms */
  animationDuration?: number;
  /** Whether to animate number changes */
  animate?: boolean;
}

const MetricCard = forwardRef<HTMLDivElement, MetricCardProps>(
  (
    {
      value,
      label,
      icon,
      trend,
      trendValue,
      variant = "neutral",
      size = "md",
      className,
      onClick,
      loading = false,
      animationDuration = 800,
      animate = true,
    },
    ref
  ) => {
    const variantStyles = {
      primary: "border-l-primary-500",
      success: "border-l-success-500",
      warning: "border-l-warning-500",
      danger: "border-l-danger-500",
      info: "border-l-info-500",
      neutral: "border-l-border-strong",
    };

    const sizeStyles = {
      sm: "p-4",
      md: "p-6",
      lg: "p-8",
    };

    const valueStyles = {
      sm: "text-2xl",
      md: "text-3xl",
      lg: "text-4xl",
    };

    const labelStyles = {
      sm: "text-xs",
      md: "text-sm",
      lg: "text-base",
    };

    const iconStyles = {
      sm: "h-5 w-5",
      md: "h-6 w-6",
      lg: "h-8 w-8",
    };

    const trendColors = {
      up: "text-success-500",
      down: "text-danger-500",
      neutral: "text-text-muted",
    };

    // Number animation logic
    const [displayValue, setDisplayValue] = useState<string | number>(value);
    const prevValueRef = useRef<string | number>(value);
    const animationFrameRef = useRef<number | null>(null);
    const startTimeRef = useRef<number | null>(null);
    const startValueRef = useRef<number>(0);
    const endValueRef = useRef<number>(0);
    const isAnimatingRef = useRef(false);

    const prefersReducedMotion = typeof window !== "undefined" 
      ? window.matchMedia("(prefers-reduced-motion: reduce)").matches 
      : false;

    const parseNumber = (val: string | number): number => {
      if (typeof val === "number") return val;
      // Handle formatted numbers like "1,234" or "1.5K"
      const cleaned = val.replace(/[,\s]/g, "");
      if (cleaned.endsWith("K")) return parseFloat(cleaned) * 1000;
      if (cleaned.endsWith("M")) return parseFloat(cleaned) * 1000000;
      if (cleaned.endsWith("B")) return parseFloat(cleaned) * 1000000000;
      return parseFloat(cleaned) || 0;
    };

    const formatNumber = (num: number): string => {
      if (num >= 1000000000) return (num / 1000000000).toFixed(1) + "B";
      if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
      if (num >= 1000) return (num / 1000).toFixed(1) + "K";
      return num.toLocaleString();
    };

    const animateNumber = (from: number, to: number, duration: number) => {
      if (isAnimatingRef.current && animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      
      isAnimatingRef.current = true;
      startValueRef.current = from;
      endValueRef.current = to;
      startTimeRef.current = performance.now();

      const step = (timestamp: number) => {
        if (!startTimeRef.current) return;
        
        const elapsed = timestamp - startTimeRef.current;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function (ease-out cubic)
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = from + (to - from) * eased;
        
        setDisplayValue(formatNumber(current));
        
        if (progress < 1) {
          animationFrameRef.current = requestAnimationFrame(step);
        } else {
          isAnimatingRef.current = false;
          setDisplayValue(value); // Ensure exact final value
        }
      };
      
      animationFrameRef.current = requestAnimationFrame(step);
    };

    useEffect(() => {
      if (!animate || prefersReducedMotion) {
        setDisplayValue(value);
        return;
      }

      const prevNum = parseNumber(prevValueRef.current);
      const currentNum = parseNumber(value);

      if (prevNum !== currentNum && !isNaN(prevNum) && !isNaN(currentNum)) {
        animateNumber(prevNum, currentNum, animationDuration);
      } else {
        setDisplayValue(value);
      }

      prevValueRef.current = value;

      return () => {
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
        }
      };
    }, [value, animate, animationDuration, prefersReducedMotion]);

    if (loading) {
      return (
        <div
          ref={ref}
          className={cn(
            "card-interactive animate-pulse",
            variantStyles[variant],
            sizeStyles[size],
            className
          )}
          aria-busy="true"
        >
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <div className="h-4 bg-muted rounded w-3/4" />
              <div className="h-8 bg-muted rounded w-1/2" />
            </div>
            <div className="h-10 w-10 bg-muted rounded-lg" />
          </div>
        </div>
      );
    }

    return (
      <div
        ref={ref}
        className={cn(
          "card-interactive",
          variantStyles[variant],
          sizeStyles[size],
          className,
          onClick && "cursor-pointer"
        )}
        onClick={onClick}
        role={onClick ? "button" : undefined}
        tabIndex={onClick ? 0 : undefined}
        onKeyDown={onClick ? (e) => (e.key === "Enter" || e.key === " ") && onClick() : undefined}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <p className={cn("text-text-secondary font-medium", labelStyles[size])}>
              {label}
            </p>
            <div className="mt-1 flex items-baseline gap-2">
              <span 
                className={cn("font-mono font-bold tabular-nums transition-all duration-150", valueStyles[size])}
                aria-live="polite"
              >
                {displayValue}
              </span>
              {trend && trendValue && (
                <span
                  className={cn(
                    "flex items-center gap-1 text-status",
                    trendColors[trend]
                  )}
                  aria-label={trend === "up" ? "Increasing" : trend === "down" ? "Decreasing" : "Stable"}
                >
                  {trend === "up" && (
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                    </svg>
                  )}
                  {trend === "down" && (
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                    </svg>
                  )}
                  {trend === "neutral" && (
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" />
                    </svg>
                  )}
                  {trendValue}
                </span>
              )}
            </div>
          </div>
          {icon && (
            <div
              className={cn(
                "flex-shrink-0 flex items-center justify-center rounded-lg",
                iconStyles[size],
                {
                  "bg-primary-100 text-primary-600 dark:bg-primary-900/30 dark:text-primary-400":
                    variant === "primary",
                  "bg-success-100 text-success-600 dark:bg-success-900/30 dark:text-success-400":
                    variant === "success",
                  "bg-warning-100 text-warning-600 dark:bg-warning-900/30 dark:text-warning-400":
                    variant === "warning",
                  "bg-danger-100 text-danger-600 dark:bg-danger-900/30 dark:text-danger-400":
                    variant === "danger",
                  "bg-info-100 text-info-600 dark:bg-info-900/30 dark:text-info-400":
                    variant === "info",
                  "bg-muted text-text-muted":
                    variant === "neutral",
                }
              )}
              aria-hidden="true"
            >
              {icon}
            </div>
          )}
        </div>
      </div>
    );
  }
);

MetricCard.displayName = "MetricCard";

export { MetricCard };
export type { MetricCardProps };
