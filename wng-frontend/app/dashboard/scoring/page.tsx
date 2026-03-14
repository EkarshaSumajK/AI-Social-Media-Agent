'use client';

import { useEffect, useState } from 'react';
import { CheckCircle2, FileText, Loader2, Search } from 'lucide-react';

import { PageHeader } from '@/components/page-header';
import { CardListSkeleton } from '@/components/skeletons';
import { StatusBadge } from '@/components/status-badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { fetchDrafts, scoreContent } from '@/lib/api';
import type { Article, ContentScoreResponse } from '@/lib/types';
import { cn } from '@/lib/utils';

const SCORE_GAUGES = [
  { key: 'virality_score' as const, label: 'Virality', color: 'bg-ember', description: 'Share & engagement potential' },
  { key: 'clarity_score' as const, label: 'Clarity', color: 'bg-ocean', description: 'Ease of reading' },
  { key: 'hook_strength_score' as const, label: 'Hook Strength', color: 'bg-moss', description: 'Opening effectiveness' },
  { key: 'conversion_score' as const, label: 'Conversion', color: 'bg-apple-blue', description: 'CTA effectiveness' },
];

function scoreColor(value: number): string {
  if (value >= 75) return 'text-emerald-400';
  if (value >= 50) return 'text-apple-blue';
  return 'text-rose-400';
}

export default function ScoringPage() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [articlesLoading, setArticlesLoading] = useState(true);
  const [articlesError, setArticlesError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [result, setResult] = useState<ContentScoreResponse | null>(null);
  const [scoring, setScoring] = useState(false);
  const [scoreError, setScoreError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setArticlesLoading(true);
      setArticlesError(null);
      try {
        const data = await fetchDrafts();
        setArticles(data);
      } catch (err) {
        setArticlesError(err instanceof Error ? err.message : 'Failed to load articles');
      } finally {
        setArticlesLoading(false);
      }
    }
    void load();
  }, []);

  const filtered = articles.filter((a) => {
    const q = search.toLowerCase();
    return !q || (a.seo_title ?? '').toLowerCase().includes(q) || (a.meta_description ?? '').toLowerCase().includes(q);
  });

  async function handleScore() {
    if (!selectedId) { setScoreError('Select an article first.'); return; }
    setScoring(true);
    setScoreError(null);
    setResult(null);
    try {
      const res = await scoreContent(selectedId);
      setResult(res);
    } catch (err) {
      setScoreError(err instanceof Error ? err.message : 'Failed to score content');
    } finally {
      setScoring(false);
    }
  }

  const selectedArticle = articles.find((a) => a.id === selectedId);

  return (
    <div className="flex flex-col gap-6 p-4 sm:p-6">
      <PageHeader
        title="Content Scoring"
        description="AI-powered quality analysis — virality, clarity, hook strength, conversion"
      />

      <section className="rounded-lg border bg-card text-card-foreground shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.06] px-5 py-4">
          <div className="flex items-center gap-2">
            <FileText size={15} className="text-apple-blue" />
            <h2 className="text-base font-semibold text-ink">Select Article to Score</h2>
          </div>
          <div className="relative w-full max-w-xs">
            <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint" />
            <Input
              className="h-8 pl-8 text-sm"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search articles..."
            />
          </div>
        </div>

        <div className="p-5">
          {articlesLoading ? (
            <CardListSkeleton count={3} />
          ) : articlesError ? (
            <p className="rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-400">{articlesError}</p>
          ) : filtered.length === 0 ? (
            <p className="text-sm text-ink-soft">
              {search ? 'No articles match your search.' : 'No articles found. Create a draft first.'}
            </p>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {filtered.map((article) => {
                const isSelected = selectedId === article.id;
                const alreadyScored =
                  article.virality_score != null || article.clarity_score != null ||
                  article.hook_strength_score != null || article.conversion_score != null;
                return (
                  <button
                    key={article.id}
                    type="button"
                    onClick={() => { setSelectedId(article.id); setResult(null); setScoreError(null); }}
                    className={cn(
                      'group relative flex flex-col gap-2 rounded-xl border p-4 text-left transition',
                      isSelected
                        ? 'border-apple-blue/50 bg-apple-blue/5 ring-1 ring-apple-blue/30'
                        : 'border-white/[0.06] bg-surface-2 hover:border-apple-blue/30 hover:bg-apple-blue/5',
                    )}
                  >
                    {isSelected && <CheckCircle2 size={15} className="absolute right-3 top-3 text-apple-blue" />}
                    <p className="line-clamp-2 pr-5 text-sm font-semibold text-ink">
                      {article.seo_title || 'Untitled Draft'}
                    </p>
                    <div className="flex items-center gap-2">
                      <StatusBadge status={article.status} />
                      {alreadyScored && (
                        <span className="rounded border border-emerald-500/20 bg-emerald-500/10 px-1.5 py-0.5 text-[10px] font-medium text-emerald-400">
                          Scored
                        </span>
                      )}
                    </div>
                    {article.meta_description && (
                      <p className="line-clamp-2 text-xs text-ink-faint">{article.meta_description}</p>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-white/[0.06] px-5 py-4">
          <p className="text-sm text-ink-soft">
            {selectedArticle ? `Selected: "${selectedArticle.seo_title || 'Untitled Draft'}"` : 'No article selected'}
          </p>
          <Button type="button" onClick={handleScore} disabled={scoring || !selectedId} className="min-w-[120px]">
            {scoring ? (
              <span className="flex items-center gap-1.5">
                <Loader2 className="h-3.5 w-3.5 animate-spin" /> Scoring...
              </span>
            ) : (
              'Score Article'
            )}
          </Button>
        </div>
      </section>

      {scoreError && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">{scoreError}</div>
      )}

      {result && (
        <section className="rounded-lg border bg-card text-card-foreground shadow-sm p-5">
          <h2 className="mb-1 text-base font-semibold text-ink">Score Results</h2>
          <p className="mb-5 text-xs text-ink-soft">Article #{result.article_id}</p>

          <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {SCORE_GAUGES.map((g) => {
              const value = result[g.key] ?? 0;
              return (
                <div key={g.key} className="rounded-xl border border-white/[0.06] bg-surface-2 p-4">
                  <p className="mb-0.5 text-sm font-semibold text-ink">{g.label}</p>
                  <p className="mb-2 text-xs text-ink-faint">{g.description}</p>
                  <div className="mb-2 h-2 overflow-hidden rounded-full bg-white/[0.08]">
                    <div className={cn('h-full rounded-full', g.color)} style={{ width: `${Math.min(100, value)}%` }} />
                  </div>
                  <p className={cn('text-2xl font-bold', scoreColor(value))}>
                    {Math.round(value)}<span className="text-sm font-normal text-ink-faint">%</span>
                  </p>
                </div>
              );
            })}
          </div>

          {result.breakdown && Object.keys(result.breakdown).length > 0 && (
            <div>
              <h3 className="mb-3 text-sm font-semibold text-ink">Detailed Breakdown</h3>
              <div className="rounded-xl border border-white/[0.06] bg-surface-2 p-4">
                <dl className="space-y-3">
                  {Object.entries(result.breakdown).map(([key, val]) => (
                    <div key={key} className="flex flex-col gap-0.5 sm:flex-row sm:gap-3">
                      <dt className="min-w-[160px] text-xs font-semibold uppercase tracking-wide text-ink-soft">
                        {key.replace(/_/g, ' ')}
                      </dt>
                      <dd className="text-sm text-ink">
                        {Array.isArray(val) ? (
                          <ul className="list-inside list-disc space-y-0.5">
                            {(val as unknown[]).map((v, i) => <li key={i}>{String(v)}</li>)}
                          </ul>
                        ) : (
                          String(val)
                        )}
                      </dd>
                    </div>
                  ))}
                </dl>
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
