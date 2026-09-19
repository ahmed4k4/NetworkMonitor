"use client";

import * as React from "react";
import { XIcon, CheckCircleIcon, AlertCircleIcon, AlertTriangleIcon, InfoIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export type ToastVariant = "default" | "success" | "warning" | "danger" | "info";

interface ToastProps {
  id: string;
  title: string;
  description?: string;
  variant?: ToastVariant;
  duration?: number;
  action?: React.ReactNode;
  onClose: (id: string) => void;
}

const variantStyles: Record<ToastVariant, string> = {
  default: "border-border bg-background",
  success: "border-success-500/30 bg-success-50 dark:bg-success-900/20",
  warning: "border-warning-500/30 bg-warning-50 dark:bg-warning-900/20",
  danger: "border-danger-500/30 bg-danger-50 dark:bg-danger-900/20",
  info: "border-info-500/30 bg-info-50 dark:bg-info-900/20",
};

const variantIcons: Record<ToastVariant, React.ReactNode> = {
  default: <InfoIcon className="h-5 w-5 text-primary-500" />,
  success: <CheckCircleIcon className="h-5 w-5 text-success-500" />,
  warning: <AlertTriangleIcon className="h-5 w-5 text-warning-500" />,
  danger: <AlertCircleIcon className="h-5 w-5 text-danger-500" />,
  info: <InfoIcon className="h-5 w-5 text-info-500" />,
};

export function Toast({
  id,
  title,
  description,
  variant = "default",
  duration = 5000,
  action,
  onClose,
}: ToastProps) {
  const [isExiting, setIsExiting] = React.useState(false);

  React.useEffect(() => {
    const timer = setTimeout(() => {
      setIsExiting(true);
      setTimeout(() => onClose(id), 200);
    }, duration);
    return () => clearTimeout(timer);
  }, [id, duration, onClose]);

  return (
    <div
      className={cn(
        "relative flex items-start gap-3 p-4 rounded-xl border shadow-lg",
        "data-[state=open]:animate-in data-[state=closed]:animate-out",
        "data-[state=closed]:fade-out-80 data-[state=closed]:slide-out-to-right-full",
        "data-[state=open]:fade-in-0 data-[state=open]:slide-in-from-right-full",
        "min-w-[320px] max-w-md",
        variantStyles[variant],
      )}
      data-state={isExiting ? "closed" : "open"}
      role="alert"
      aria-live="polite"
      aria-atomic="true"
    >
      <div className="flex-shrink-0 mt-0.5" aria-hidden="true">
        {variantIcons[variant]}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start gap-2">
          <h4 className="font-semibold text-text-primary text-sm">{title}</h4>
          <Button
            variant="ghost"
            size="icon-xs"
            className="flex-shrink-0 text-text-muted hover:text-text-primary focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
            onClick={() => {
              setIsExiting(true);
              setTimeout(() => onClose(id), 200);
            }}
            aria-label="Dismiss notification"
          >
            <XIcon className="h-4 w-4" />
            <span className="sr-only">Dismiss</span>
          </Button>
        </div>
        {description && (
          <p className="mt-1 text-sm text-text-secondary">{description}</p>
        )}
        {action && (
          <div className="mt-3">{action}</div>
        )}
      </div>
    </div>
  );
}

interface ToastViewportProps {
  children: React.ReactNode;
}

export function ToastViewport({ children }: ToastViewportProps) {
  return (
    <div
      className="fixed bottom-4 right-4 z-[800] flex flex-col gap-2 pointer-events-none"
      aria-live="polite"
      aria-atomic="true"
    >
      {children}
    </div>
  );
}

interface ToastProviderProps {
  children: React.ReactNode;
}

interface ToastContextValue {
  toasts: Toast[];
  addToast: (title: string, options?: Omit<Toast, "id" | "onClose" | "title">) => string;
  removeToast: (id: string) => void;
}

interface Toast {
  id: string;
  title: string;
  description?: string;
  variant?: ToastVariant;
  duration?: number;
  action?: React.ReactNode;
}

const ToastContext = React.createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: ToastProviderProps) {
  const [toasts, setToasts] = React.useState<Toast[]>([]);

  const addToast = React.useCallback((title: string, options?: Omit<Toast, "id" | "onClose" | "title">) => {
    const id = Math.random().toString(36).substring(2, 9);
    const toast = { ...options, title, id };
    setToasts((prev) => [...prev, toast]);
    return id;
  }, []);

  const removeToast = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastViewport>
        {toasts.map((toast) => (
          <Toast key={toast.id} {...toast} onClose={removeToast} />
        ))}
      </ToastViewport>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = React.useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}

export function toast(title: string, options?: Partial<Toast>) {
  // This will be replaced by the actual context call
  console.warn("toast() called outside of ToastProvider");
}