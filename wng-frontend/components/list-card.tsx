'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export interface ListCardAction {
  label: string;
  href?: string;
  onClick?: () => void;
  variant?: 'default' | 'outline' | 'secondary' | 'destructive' | 'ghost' | 'link';
  disabled?: boolean;
  loading?: boolean;
  icon?: React.ReactNode;
}

export interface ListCardProps {
  title: string;
  /** Optional status badge (e.g. draft, active) */
  status?: string;
  statusClassName?: string;
  /** Metadata line (grey text, e.g. "horizon • goal • date") */
  metadata?: React.ReactNode;
  /** Optional tags/badges below metadata */
  tags?: React.ReactNode;
  /** Optional extra content (e.g. "Last run generated X pieces") */
  footer?: React.ReactNode;
  /** Primary: View details. Secondary: context action (Generate, Run analysis, etc.) */
  actions: ListCardAction[];
  /** If set, the whole card links to this URL (title becomes clickable) */
  href?: string;
  className?: string;
}

/**
 * Consistent list item card matching the campaigns UI pattern.
 * Use across Competitors, Drafts, Hooks, Swipe files, etc.
 */
export function ListCard({
  title,
  status,
  statusClassName,
  metadata,
  tags,
  footer,
  actions,
  href,
  className,
}: ListCardProps) {
  const router = useRouter();

  const content = (
    <Card
      className={cn(
        'border-white/[0.06] bg-card transition-colors hover:border-apple-blue/20',
        href && 'cursor-pointer',
        className
      )}
    >
      <CardHeader className="flex flex-row items-start justify-between gap-2 pb-2">
        <h3 className="font-semibold text-ink">{title}</h3>
        {status && (
          <span
            className={cn(
              'shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium',
              statusClassName ?? 'border border-white/[0.08] bg-white/[0.04] text-ink-soft'
            )}
          >
            {status}
          </span>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        {metadata && (
          <div className="flex flex-wrap items-center gap-2 text-xs text-ink-faint">
            {metadata}
          </div>
        )}
        {tags && <div className="flex flex-wrap gap-1.5">{tags}</div>}
        {footer}
        <div className="flex flex-wrap gap-2 pt-2">
          {actions.map((action, i) => {
            const label = (
              <>
                {action.icon}
                {action.icon && <span className="ml-1.5" />}
                {action.label}
              </>
            );
            const displayLabel = action.loading ? (
              <>
                {action.icon}
                {action.icon && <span className="ml-1.5" />}
                Loading...
              </>
            ) : (
              label
            );
            return action.href ? (
              <Button
                key={i}
                variant={action.variant ?? (i === 0 ? 'outline' : 'secondary')}
                size="sm"
                asChild
              >
                <Link href={action.href} onClick={(e) => href && e.stopPropagation()}>
                  {label}
                </Link>
              </Button>
            ) : (
              <Button
                key={i}
                variant={action.variant ?? (i === 0 ? 'outline' : 'secondary')}
                size="sm"
                onClick={action.onClick}
                disabled={action.disabled || action.loading}
              >
                {displayLabel}
              </Button>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );

  if (href) {
    return (
      <div
        role="link"
        tabIndex={0}
        className="block"
        onClick={() => router.push(href)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            router.push(href);
          }
        }}
      >
        {content}
      </div>
    );
  }

  return content;
}
