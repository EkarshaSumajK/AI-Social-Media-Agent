import clsx from 'clsx';

import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

type StatusVariant = {
  dot: string;
  badge: string;
};

const VARIANTS: Record<string, StatusVariant> = {
  new: { dot: 'bg-sky-400', badge: 'border-sky-400/20 bg-sky-400/10 text-sky-300' },
  processed: { dot: 'bg-slate-400', badge: 'border-slate-400/20 bg-slate-400/10 text-slate-400' },
  duplicate_rejected: { dot: 'bg-apple-blue-400', badge: 'border-apple-blue-400/20 bg-apple-blue-400/10 text-apple-blue-400' },
  draft: { dot: 'bg-slate-500', badge: 'border-slate-500/20 bg-slate-500/10 text-slate-400' },
  approved: { dot: 'bg-emerald-400', badge: 'border-emerald-400/20 bg-emerald-400/10 text-emerald-400' },
  rejected: { dot: 'bg-rose-400', badge: 'border-rose-400/20 bg-rose-400/10 text-rose-400' },
  published: { dot: 'bg-green-400', badge: 'border-green-400/20 bg-green-400/10 text-green-400' },
  posted: { dot: 'bg-green-400', badge: 'border-green-400/20 bg-green-400/10 text-green-300' },
  failed: { dot: 'bg-red-400', badge: 'border-red-400/20 bg-red-400/10 text-red-400' },
  ready: { dot: 'bg-blue-400', badge: 'border-blue-400/20 bg-blue-400/10 text-blue-400' },
  pending: { dot: 'bg-yellow-400', badge: 'border-yellow-400/20 bg-yellow-400/10 text-yellow-400' },
  active: { dot: 'bg-apple-blue-400', badge: 'border-apple-blue-400/20 bg-apple-blue-400/10 text-apple-blue-400' },
};

const DEFAULT_VARIANT: StatusVariant = {
  dot: 'bg-slate-500',
  badge: 'border-slate-500/20 bg-slate-500/10 text-slate-400',
};

interface StatusBadgeProps {
  status: string;
  pulse?: boolean;
}

export function StatusBadge({ status, pulse }: StatusBadgeProps) {
  const v = VARIANTS[status.toLowerCase()] ?? DEFAULT_VARIANT;

  return (
    <Badge
      variant="outline"
      className={cn(
        'gap-1.5 py-1 text-[10px] uppercase tracking-[0.1em]',
        v.badge,
      )}
    >
      <span
        className={clsx(
          'inline-block h-1.5 w-1.5 rounded-full flex-shrink-0',
          v.dot,
          pulse && 'animate-pulse-dot',
        )}
      />
      {status.replaceAll('_', ' ')}
    </Badge>
  );
}
