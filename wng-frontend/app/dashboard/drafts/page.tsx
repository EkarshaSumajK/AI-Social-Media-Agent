'use client';

import { useEffect, useMemo, useState } from 'react';
import { Loader2, FileText, Filter } from 'lucide-react';

import { ListCard } from '@/components/list-card';
import { PageHeader } from '@/components/page-header';
import { PageShell } from '@/components/page-shell';
import { Button } from '@/components/ui/button';
import { fetchDrafts } from '@/lib/api';
import type { Article } from '@/lib/types';

export default function DraftsPage() {
  const [drafts, setDrafts] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');

  useEffect(() => {
    (async () => {
      try {
        const data = await fetchDrafts();
        setDrafts(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load drafts');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const filtered = useMemo(() => {
    if (statusFilter === 'all') return drafts;
    return drafts.filter((d) => d.status === statusFilter);
  }, [drafts, statusFilter]);

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: drafts.length };
    for (const d of drafts) c[d.status] = (c[d.status] || 0) + 1;
    return c;
  }, [drafts]);

  return (
    <PageShell>
      <PageHeader title="Draft Queue" description="Review, approve, and publish content">
        <div className="flex items-center gap-1.5">
          <Filter size={14} className="text-ink-faint" />
          <span className="text-xs text-ink-soft">{filtered.length} drafts</span>
        </div>
      </PageHeader>

      <div className="flex flex-col gap-6 px-4 sm:px-6 lg:px-8">
        {error && (
          <div className="rounded-lg border border-ember/30 bg-ember/5 px-4 py-3 text-sm text-ember">
            {error}
          </div>
        )}

        <div className="flex flex-wrap gap-2">
          {['all', 'draft', 'approved', 'rejected', 'published'].map((s) => (
            <Button
              key={s}
              variant="ghost"
              size="sm"
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                statusFilter === s
                  ? 'border border-apple-blue/20 bg-apple-blue/10 text-apple-blue'
                  : 'border border-white/[0.06] bg-surface-2 text-ink-soft hover:border-white/[0.08]'
              }`}
              onClick={() => setStatusFilter(s)}
            >
              {s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)} ({counts[s] || 0})
            </Button>
          ))}
        </div>

        {loading ? (
          <div className="flex items-center gap-2 py-12 text-sm text-ink-soft">
            <Loader2 size={16} className="animate-spin" />
            Loading drafts...
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center gap-4 rounded-lg border border-dashed border-white/[0.08] bg-white/[0.02] py-16">
            <FileText size={40} className="text-ink-faint" />
            <p className="text-sm text-ink-soft">No drafts found for the selected filter.</p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {filtered.map((draft) => (
              <ListCard
                key={draft.id}
                title={draft.seo_title}
                status={draft.status}
                statusClassName={
                  draft.status === 'approved'
                    ? 'border-emerald-500/10 bg-emerald-500/10 text-emerald-400'
                    : draft.status === 'published'
                      ? 'border-emerald-500/10 bg-emerald-500/10 text-emerald-400'
                      : draft.status === 'rejected'
                        ? 'border-ember/20 bg-ember/10 text-ember'
                        : undefined
                }
                metadata={
                  <>
                    <span>{draft.platform}</span>
                    {draft.topic?.source_name && (
                      <>
                        <span>•</span>
                        <span>{draft.topic.source_name}</span>
                      </>
                    )}
                    <span>•</span>
                    <span>{new Date(draft.updated_at).toLocaleDateString()}</span>
                  </>
                }
                tags={
                  <>
                    <span className="rounded-md border border-apple-blue/20 bg-apple-blue/10 px-2 py-0.5 text-xs font-medium text-apple-blue">
                      {draft.platform}
                    </span>
                    {draft.virality_score != null && (
                      <span className="rounded-md border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5 text-xs text-emerald-400">
                        Virality {(draft.virality_score * 100).toFixed(0)}%
                      </span>
                    )}
                    {draft.clarity_score != null && (
                      <span className="rounded-md border border-blue-500/20 bg-blue-500/10 px-2 py-0.5 text-xs text-blue-400">
                        Clarity {(draft.clarity_score * 100).toFixed(0)}%
                      </span>
                    )}
                  </>
                }
                footer={
                  draft.meta_description ? (
                    <p className="line-clamp-2 text-xs text-ink-soft">{draft.meta_description}</p>
                  ) : undefined
                }
                actions={[{ label: 'View details', href: `/dashboard/drafts/${draft.id}` }]}
                href={`/dashboard/drafts/${draft.id}`}
              />
            ))}
          </div>
        )}
      </div>
    </PageShell>
  );
}
