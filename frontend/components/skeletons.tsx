import { Skeleton } from '@/components/ui/skeleton';

/* -------------------------------------------------------------------------- */
/*  CardListSkeleton                                                          */
/* -------------------------------------------------------------------------- */

interface CardListSkeletonProps {
  /** Number of card skeletons to render. Defaults to 3. */
  count?: number;
}

export function CardListSkeleton({ count = 3 }: CardListSkeletonProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="rounded-xl border border-border bg-card p-5 space-y-4"
        >
          <Skeleton className="h-5 w-3/5" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-4/5" />
          <div className="flex items-center gap-2 pt-2">
            <Skeleton className="h-8 w-8 rounded-full" />
            <Skeleton className="h-4 w-24" />
          </div>
        </div>
      ))}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  MetricGridSkeleton                                                        */
/* -------------------------------------------------------------------------- */

export function MetricGridSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div
          key={i}
          className="rounded-xl border border-border bg-card p-5 space-y-3"
        >
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-8 w-20" />
          <Skeleton className="h-3 w-16" />
        </div>
      ))}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  FormSkeleton                                                              */
/* -------------------------------------------------------------------------- */

export function FormSkeleton() {
  return (
    <div className="max-w-2xl space-y-6">
      {/* Field groups */}
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="space-y-2">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-10 w-full rounded-md" />
        </div>
      ))}

      {/* Textarea field */}
      <div className="space-y-2">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-28 w-full rounded-md" />
      </div>

      {/* Actions row */}
      <div className="flex items-center gap-3 pt-2">
        <Skeleton className="h-10 w-28 rounded-md" />
        <Skeleton className="h-10 w-20 rounded-md" />
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  TableSkeleton                                                             */
/* -------------------------------------------------------------------------- */

interface TableSkeletonProps {
  /** Number of rows to render. Defaults to 5. */
  rows?: number;
  /** Number of columns to render. Defaults to 4. */
  columns?: number;
}

export function TableSkeleton({ rows = 5, columns = 4 }: TableSkeletonProps) {
  return (
    <div className="w-full rounded-xl border border-border bg-card overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-4 border-b border-border px-4 py-3">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton
            key={i}
            className="h-4"
            style={{ width: i === 0 ? '30%' : `${60 / (columns - 1)}%` }}
          />
        ))}
      </div>

      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIdx) => (
        <div
          key={rowIdx}
          className="flex items-center gap-4 border-b border-border px-4 py-3 last:border-b-0"
        >
          {Array.from({ length: columns }).map((_, colIdx) => (
            <Skeleton
              key={colIdx}
              className="h-4"
              style={{
                width: colIdx === 0 ? '30%' : `${60 / (columns - 1)}%`,
              }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
