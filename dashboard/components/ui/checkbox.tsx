"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { CheckIcon } from "lucide-react";

export interface CheckboxProps {
  checked?: boolean;
  indeterminate?: boolean;
  onCheckedChange?: (checked: boolean) => void;
  disabled?: boolean;
  className?: string;
  id?: string;
  name?: string;
  value?: string;
  "aria-label"?: string;
  "aria-labelledby"?: string;
}

export function Checkbox({
  checked = false,
  indeterminate = false,
  onCheckedChange,
  disabled = false,
  className,
  id,
  name,
  value = "on",
  "aria-label": ariaLabel,
  "aria-labelledby": ariaLabelledBy,
}: CheckboxProps) {
  const checkboxRef = React.useRef<HTMLButtonElement>(null);
  const nativeCheckboxRef = React.useRef<HTMLInputElement>(null);

  // Handle indeterminate state
  React.useEffect(() => {
    if (nativeCheckboxRef.current) {
      nativeCheckboxRef.current.indeterminate = indeterminate;
    }
  }, [indeterminate]);

  const handleClick = () => {
    if (disabled) return;
    const newChecked = !checked;
    onCheckedChange?.(newChecked);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
    if (e.key === " " || e.key === "Enter") {
      e.preventDefault();
      handleClick();
    }
  };

  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={indeterminate ? "mixed" : checked}
      aria-disabled={disabled}
      aria-label={ariaLabel}
      aria-labelledby={ariaLabelledBy}
      disabled={disabled}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      ref={checkboxRef}
      className={cn(
        "relative inline-flex h-5 w-5 shrink-0 cursor-pointer items-center justify-center rounded border-2 transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        "disabled:cursor-not-allowed disabled:opacity-50",
        checked
          ? "bg-primary border-primary text-primary-foreground"
          : "bg-background border-input hover:border-primary/50",
        className
      )}
    >
      {checked && (
        <CheckIcon
          className="h-3.5 w-3.5 text-current stroke-2 transition-opacity"
          aria-hidden="true"
        />
      )}
      {indeterminate && !checked && (
        <div
          className="h-0.5 w-2.5 bg-current rounded transition-opacity"
          aria-hidden="true"
        />
      )}
      {/* Hidden native checkbox for form submission and indeterminate state */}
      <input
        ref={nativeCheckboxRef}
        type="checkbox"
        className="absolute inset-0 opacity-0 pointer-events-none"
        checked={checked}
        disabled={disabled}
        id={id}
        name={name}
        value={value}
        tabIndex={-1}
        onChange={() => {}}
      />
    </button>
  );
}

// For use in forms with native form submission
export function FormCheckbox({
  checked = false,
  onCheckedChange,
  disabled = false,
  className,
  id,
  name,
  value = "on",
  required = false,
  "aria-label": ariaLabel,
  "aria-labelledby": ariaLabelledBy,
}: CheckboxProps & { required?: boolean }) {
  return (
    <>
      <Checkbox
        checked={checked}
        onCheckedChange={onCheckedChange}
        disabled={disabled}
        className={className}
        id={id}
        name={name}
        value={value}
        aria-label={ariaLabel}
        aria-labelledby={ariaLabelledBy}
      />
      {/* Hidden input for form submission */}
      <input
        type="checkbox"
        name={name}
        value={value}
        checked={checked}
        disabled={disabled}
        required={required}
        className="absolute opacity-0 pointer-events-none h-0 w-0"
        tabIndex={-1}
        aria-hidden="true"
      />
    </>
  );
}
