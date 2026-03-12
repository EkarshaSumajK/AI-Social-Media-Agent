'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ArrowLeft, Copy, Loader2 } from 'lucide-react';

import { PageHeader } from '@/components/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { fetchHook } from '@/lib/api';
import type { HookTemplate } from '@/lib/types';

function labelize(value: string) {
  return value
    .split('_')
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(' ');
}

export default function HookDetailPage() {
  const params = useParams<{ id: string }>();
  const hookId = Number(params.id);

  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hook, setHook] = useState<HookTemplate | null>(null);

  useEffect(() => {
    async function loadHook() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchHook(hookId);
        setHook(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load hook');
      } finally {
        setLoading(false);
      }
    }

    if (Number.isNaN(hookId)) {
      setLoading(false);
      setError('Invalid hook id');
      return;
    }

    void loadHook();
  }, [hookId]);

  async function handleCopy() {
    if (!hook) return;
    try {
      await navigator.clipboard.writeText(hook.hook_text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setError('Unable to copy hook text');
    }
  }

  return (
    <div className="flex flex-col">
      <PageHeader title={hook ? 'Hook Detail' : 'Hook Detail'} description="Detailed hook metadata and usage context">
        <Button asChild variant="outline" size="sm">
          <Link href="/dashboard/hooks">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to hooks
          </Link>
        </Button>
      </PageHeader>

      <div className="flex flex-col gap-6 p-4 sm:p-6">
        {error && <div className="rounded-xl border border-ember/30 bg-ember/5 px-4 py-3 text-sm text-ember">{error}</div>}

        {loading ? (
          <div className="flex items-center gap-2 text-sm text-ink-soft">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading hook...
          </div>
        ) : hook ? (
          <>
            <section className="rounded-lg border bg-card p-5 text-card-foreground shadow-sm">
              <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                <h2 className="max-w-3xl text-lg font-semibold text-ink">{hook.hook_text}</h2>
                <Button type="button" variant="secondary" size="sm" onClick={handleCopy}>
                  <Copy className="mr-2 h-4 w-4" />
                  {copied ? 'Copied' : 'Copy'}
                </Button>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="outline">{labelize(hook.category)}</Badge>
                <Badge variant="secondary">{labelize(hook.platform)}</Badge>
                <span className="text-xs text-ink-soft">Used {hook.use_count} times</span>
                {hook.industry && <span className="text-xs text-ink-soft">Industry: {hook.industry}</span>}
              </div>
            </section>

            <section className="rounded-lg border bg-card p-5 text-card-foreground shadow-sm">
              <h2 className="mb-3 text-lg font-semibold text-ink">Suggested next action</h2>
              <p className="mb-4 text-sm text-ink-soft">
                Use this hook in the platform generator or include it in a thought-leadership draft to test performance.
              </p>
              <div className="flex flex-wrap gap-2">
                <Button asChild variant="outline" size="sm">
                  <Link href="/dashboard/platform-content">Open platform generator</Link>
                </Button>
                <Button asChild variant="outline" size="sm">
                  <Link href="/dashboard/thought-leadership">Open thought leadership</Link>
                </Button>
              </div>
            </section>
          </>
        ) : (
          <p className="text-sm text-ink-soft">Hook not found.</p>
        )}
      </div>
    </div>
  );
}
