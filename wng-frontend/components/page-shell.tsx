'use client';

import { cn } from '@/lib/utils';

interface PageShellProps {
  children: React.ReactNode;
  className?: string;
  /** Whether to apply the page-enter fade-up animation. Defaults to true. */
  animate?: boolean;
}

export function PageShell({ children, className, animate = true }: PageShellProps) {
  return (
    <div
      className={cn(
        'px-4 py-6 sm:px-6 lg:px-8',
        animate && 'page-enter',
        className,
      )}
    >
      {children}
    </div>
  );
}
