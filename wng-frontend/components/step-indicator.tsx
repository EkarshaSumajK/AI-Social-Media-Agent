'use client';

import { cn } from '@/lib/utils';
import { Check } from 'lucide-react';

interface Step {
  label: string;
  description?: string;
}

interface StepIndicatorProps {
  steps: Step[];
  /** The active step (0-indexed). */
  currentStep: number;
}

export function StepIndicator({ steps, currentStep }: StepIndicatorProps) {
  return (
    <nav aria-label="Progress" className="w-full">
      <ol className="flex items-center">
        {steps.map((step, index) => {
          const isCompleted = index < currentStep;
          const isCurrent = index === currentStep;
          const isUpcoming = index > currentStep;
          const isLast = index === steps.length - 1;

          return (
            <li
              key={step.label}
              className={cn('relative flex items-center', !isLast && 'flex-1')}
            >
              {/* Dot / check */}
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    'flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 text-xs font-semibold transition-colors',
                    isCompleted &&
                      'border-apple-blue bg-apple-blue text-white',
                    isCurrent &&
                      'border-apple-blue bg-apple-blue/10 text-apple-blue animate-pulse',
                    isUpcoming &&
                      'border-muted-foreground/30 bg-transparent text-muted-foreground/50',
                  )}
                >
                  {isCompleted ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <span>{index + 1}</span>
                  )}
                </div>

                {/* Label + description (below dot) */}
                <div className="mt-2 text-center">
                  <span
                    className={cn(
                      'block text-xs font-medium leading-tight',
                      isCompleted && 'text-apple-blue',
                      isCurrent && 'text-foreground',
                      isUpcoming && 'text-muted-foreground/60',
                    )}
                  >
                    {step.label}
                  </span>
                  {step.description && (
                    <span
                      className={cn(
                        'mt-0.5 block text-[11px] leading-tight',
                        isCurrent
                          ? 'text-muted-foreground'
                          : 'text-muted-foreground/50',
                      )}
                    >
                      {step.description}
                    </span>
                  )}
                </div>
              </div>

              {/* Connector line */}
              {!isLast && (
                <div
                  className={cn(
                    'mx-2 h-0.5 flex-1 self-start mt-4 transition-colors',
                    isCompleted ? 'bg-apple-blue' : 'bg-muted-foreground/20',
                  )}
                  aria-hidden="true"
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
