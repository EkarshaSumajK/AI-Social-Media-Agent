'use client';

import { cn } from '@/lib/utils';

interface PageHeaderProps {
  title: string;
  description?: string;
  eyebrow?: string;
  children?: React.ReactNode;
}

export function PageHeader({ title, description, eyebrow, children }: PageHeaderProps) {
  return (
    <header className="relative overflow-hidden border-b border-white/[0.06]">
      {/* Gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-apple-blue/[0.06] via-transparent to-transparent" />
      {/* Top accent line */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-apple-blue/50 via-apple-blue/20 to-transparent" />
      {/* Decorative radial glow */}
      <div className="absolute -left-12 -top-12 h-48 w-48 rounded-full bg-apple-blue/[0.04] blur-3xl" />

      <div
        className={cn(
          'relative px-5 py-5 sm:px-6',
          children && 'flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between',
        )}
      >
        <div className="min-w-0">
          {eyebrow && (
            <div className="mb-2 flex items-center gap-2">
              <span className="h-px w-4 bg-apple-blue/50" />
              <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-apple-blue/80">
                {eyebrow}
              </p>
            </div>
          )}
          <h1
            className="truncate text-[1.375rem] font-bold leading-tight tracking-tight text-ink sm:text-2xl"
            style={{ fontFamily: 'var(--font-display)' }}
          >
            {title}
          </h1>
          {description && (
            <p className="mt-1.5 text-[13px] leading-relaxed text-ink-soft">
              {description}
            </p>
          )}
        </div>

        {children && (
          <div className="flex shrink-0 flex-wrap items-center gap-2">
            {children}
          </div>
        )}
      </div>
    </header>
  );
}
