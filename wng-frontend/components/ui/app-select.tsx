"use client"

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"

type SelectOption = {
  value: string
  label: string
}

interface AppSelectProps {
  value: string
  onValueChange: (value: string) => void
  options: SelectOption[]
  placeholder?: string
  triggerClassName?: string
  disabled?: boolean
}

const EMPTY_VALUE = "__EMPTY__"

export function AppSelect({
  value,
  onValueChange,
  options,
  placeholder,
  triggerClassName,
  disabled,
}: AppSelectProps) {
  const normalizedValue = value === "" ? EMPTY_VALUE : value

  return (
    <Select
      value={normalizedValue}
      onValueChange={(next) => onValueChange(next === EMPTY_VALUE ? "" : next)}
      disabled={disabled}
    >
      <SelectTrigger className={cn("bg-surface-2 text-ink", triggerClassName)}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {options.map((option) => (
          <SelectItem
            key={option.value || EMPTY_VALUE}
            value={option.value === "" ? EMPTY_VALUE : option.value}
          >
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
