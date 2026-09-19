"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { AlertCircleIcon, CheckIcon, XIcon } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"

export interface FormFieldConfig<T extends string = string> {
  name: T
  label: string
  type?: "text" | "email" | "password" | "number" | "tel" | "url"
  placeholder?: string
  required?: boolean
  disabled?: boolean
  helperText?: string
  errorMessage?: string
  validate?: (value: string) => string | undefined
  transform?: (value: string) => string
}

export interface FormConfig<T extends Record<string, unknown> = Record<string, unknown>> {
  fields: FormFieldConfig<keyof T & string>[]
  onSubmit: (data: T) => Promise<void> | void
  submitLabel?: string
  submitVariant?: "default" | "outline" | "secondary" | "ghost" | "destructive"
}

interface FormFieldProps<T extends string> {
  config: FormFieldConfig<T>
  value: string
  error: string | undefined
  touched: boolean
  onChange: (name: T, value: string) => void
  onBlur: (name: T) => void
}

function FormField<T extends string>({
  config,
  value,
  error,
  touched,
  onChange,
  onBlur,
}: FormFieldProps<T>) {
  const showError = touched && !!error
  const showSuccess = touched && !error && config.required && value.length > 0
  const showHelper = config.helperText && !showError

  return (
    <div className="w-full">
      <Label htmlFor={config.name} className="mb-1.5 block">
        {config.label}
        {config.required && (
          <span className="ml-1 text-danger-500" aria-hidden="true">*</span>
        )}
      </Label>
      <Input
        id={config.name}
        name={config.name}
        type={config.type ?? "text"}
        placeholder={config.placeholder}
        value={value}
        onChange={(e) => onChange(config.name, e.target.value)}
        onBlur={() => onBlur(config.name)}
        disabled={config.disabled}
        aria-invalid={showError}
        aria-describedby={showError ? `${config.name}-error` : showHelper ? `${config.name}-helper` : undefined}
        className={cn(
          showError && "border-destructive/50 focus-visible:border-destructive focus-visible:ring-destructive/20",
          showSuccess && "border-success-500/50 focus-visible:border-success-500 focus-visible:ring-success-500/20"
        )}
      />
      {showError && (
        <p id={`${config.name}-error`} className="mt-1.5 flex items-center gap-1.5 text-sm text-destructive" role="alert">
          <AlertCircleIcon className="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </p>
      )}
      {showSuccess && (
        <p className="mt-1.5 flex items-center gap-1.5 text-sm text-success-500" aria-live="polite">
          <CheckIcon className="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
          <span>Valid</span>
        </p>
      )}
      {showHelper && (
        <p id={`${config.name}-helper`} className="mt-1.5 text-sm text-muted-foreground">
          {config.helperText}
        </p>
      )}
    </div>
  )
}

export function Form<T extends Record<string, unknown>>({
  fields,
  onSubmit,
  submitLabel = "Submit",
  submitVariant = "default",
}: FormConfig<T>) {
  const [values, setValues] = React.useState<Partial<T>>({})
  const [errors, setErrors] = React.useState<Partial<Record<keyof T, string>>>({})
  const [touched, setTouched] = React.useState<Partial<Record<keyof T, boolean>>>({})
  const [isSubmitting, setIsSubmitting] = React.useState(false)
  const [submitError, setSubmitError] = React.useState<string | undefined>()
  const formRef = React.useRef<HTMLFormElement>(null)

  const validateField = (name: keyof T & string, value: string): string | undefined => {
    const fieldConfig = fields.find(f => f.name === name)
    if (!fieldConfig) return undefined

    if (fieldConfig.required && !value.trim()) {
      return `${fieldConfig.label} is required`
    }

    if (fieldConfig.validate) {
      return fieldConfig.validate(value)
    }

    return undefined
  }

  const handleChange = (name: keyof T & string, value: string) => {
    const fieldConfig = fields.find(f => f.name === name)
    const transformedValue = fieldConfig?.transform ? fieldConfig.transform(value) : value
    
    setValues(prev => ({ ...prev, [name]: transformedValue }))
    
    // Validate on change if field was already touched
    if (touched[name]) {
      const error = validateField(name, transformedValue)
      setErrors(prev => ({ ...prev, [name]: error }))
    }
  }

  const handleBlur = (name: keyof T & string) => {
    setTouched(prev => ({ ...prev, [name]: true }))
    const value = values[name] as string ?? ""
    const error = validateField(name, value)
    setErrors(prev => ({ ...prev, [name]: error }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitError(undefined)

    // Mark all fields as touched and validate
    const newTouched: Partial<Record<keyof T, boolean>> = {}
    const newErrors: Partial<Record<keyof T, string>> = {}
    let hasErrors = false

    for (const field of fields) {
      newTouched[field.name] = true
      const value = (values[field.name] as string) ?? ""
      const error = validateField(field.name, value)
      if (error) {
        newErrors[field.name] = error
        hasErrors = true
      }
    }

    setTouched(prev => ({ ...prev, ...newTouched }))
    setErrors(prev => ({ ...prev, ...newErrors }))

    if (hasErrors) {
      // Focus first error field
      const firstErrorField = fields.find(f => newErrors[f.name])
      if (firstErrorField) {
        const input = formRef.current?.querySelector(`#${firstErrorField.name}`) as HTMLElement
        input?.focus()
      }
      return
    }

    setIsSubmitting(true)
    try {
      await onSubmit(values as T)
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "An error occurred")
    } finally {
      setIsSubmitting(false)
    }
  }

  const resetForm = () => {
    setValues({})
    setErrors({})
    setTouched({})
    setSubmitError(undefined)
  }

  return (
    <form ref={formRef} onSubmit={handleSubmit} className="space-y-4" noValidate>
      {submitError && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800" role="alert">
          <AlertCircleIcon className="h-5 w-5 text-destructive flex-shrink-0" aria-hidden="true" />
          <p className="text-sm text-destructive">{submitError}</p>
        </div>
      )}

      <div className="space-y-4">
        {fields.map((field) => (
          <FormField
            key={field.name}
            config={field}
            value={(values[field.name] as string) ?? ""}
            error={errors[field.name]}
            touched={!!touched[field.name]}
            onChange={handleChange}
            onBlur={handleBlur}
          />
        ))}
      </div>

      <div className="flex items-center gap-3 pt-2">
        <Button
          type="submit"
          variant={submitVariant}
          loading={isSubmitting}
          loadingText="Submitting..."
          disabled={isSubmitting}
        >
          {submitLabel}
        </Button>
        <Button
          type="button"
          variant="ghost"
          onClick={resetForm}
          disabled={isSubmitting}
        >
          Reset
        </Button>
      </div>
    </form>
  )
}

// Common validation helpers
export const validators = {
  email: (value: string): string | undefined => {
    if (!value) return undefined
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(value)) return "Invalid email address"
    return undefined
  },

  minLength: (min: number) => (value: string): string | undefined => {
    if (!value) return undefined
    if (value.length < min) return `Must be at least ${min} characters`
    return undefined
  },

  maxLength: (max: number) => (value: string): string | undefined => {
    if (!value) return undefined
    if (value.length > max) return `Must be no more than ${max} characters`
    return undefined
  },

  pattern: (regex: RegExp, message: string) => (value: string): string | undefined => {
    if (!value) return undefined
    if (!regex.test(value)) return message
    return undefined
  },

  url: (value: string): string | undefined => {
    if (!value) return undefined
    try {
      new URL(value)
      return undefined
    } catch {
      return "Invalid URL"
    }
  },

  number: (value: string): string | undefined => {
    if (!value) return undefined
    if (isNaN(Number(value))) return "Must be a valid number"
    return undefined
  },

  ipAddress: (value: string): string | undefined => {
    if (!value) return undefined
    const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/
    const ipv6Regex = /^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/
    if (!ipv4Regex.test(value) && !ipv6Regex.test(value)) return "Invalid IP address"
    if (ipv4Regex.test(value)) {
      const parts = value.split(".")
      if (parts.some(p => parseInt(p, 10) > 255)) return "Invalid IP address"
    }
    return undefined
  },

  macAddress: (value: string): string | undefined => {
    if (!value) return undefined
    const macRegex = /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/
    if (!macRegex.test(value)) return "Invalid MAC address (format: AA:BB:CC:DD:EE:FF)"
    return undefined
  },

  cidr: (value: string): string | undefined => {
    if (!value) return undefined
    const cidrRegex = /^(\d{1,3}\.){3}\d{1,3}\/\d{1,2}$/
    if (!cidrRegex.test(value)) return "Invalid CIDR (format: 192.168.1.0/24)"
    const [ip, prefix] = value.split("/")
    const ipParts = ip.split(".")
    if (ipParts.some(p => parseInt(p, 10) > 255)) return "Invalid IP address"
    if (parseInt(prefix, 10) > 32) return "Prefix must be 0-32"
    return undefined
  },
}

// Transform helpers
export const transforms = {
  trim: (value: string) => value.trim(),
  lowercase: (value: string) => value.toLowerCase(),
  uppercase: (value: string) => value.toUpperCase(),
  removeSpaces: (value: string) => value.replace(/\s+/g, ""),
  toNumber: (value: string) => value,
}