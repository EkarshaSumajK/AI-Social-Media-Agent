'use client';

import { useEffect, useState } from 'react';
import { Check, Copy, Loader2 } from 'lucide-react';

import { ListCard } from '@/components/list-card';
import { PageHeader } from '@/components/page-header';
import { PageShell } from '@/components/page-shell';
import { CardListSkeleton } from '@/components/skeletons';
import { AppSelect } from '@/components/ui/app-select';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { fetchDailyPostsHistory, generateDailyPosts } from '@/lib/api';
import type { DailyPostBatch, DailyPostSuggestion } from '@/lib/types';
import { REGIONS } from '@/lib/types';
import { cn } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

const BUSINESS_GOALS = [
  { value: 'brand', label: 'Brand Awareness' },
  { value: 'leads', label: 'Lead Generation' },
  { value: 'sales', label: 'Sales Conversion' },
] as const;

const POST_TYPE_STYLES: Record<string, { label: string; badge: string; dot: string }> = {
  trending_topic:    { label: 'Trending Topic',    badge: 'bg-apple-blue/15 text-apple-blue border-apple-blue/20',                dot: 'bg-apple-blue' },
  authority:         { label: 'Authority',          badge: 'bg-moss/15 text-moss border-moss/20',                  dot: 'bg-moss' },
  engagement:        { label: 'Engagement',         badge: 'bg-ocean/15 text-ocean border-ocean/20',               dot: 'bg-ocean' },
  storytelling:      { label: 'Storytelling',       badge: 'bg-violet-500/15 text-violet-400 border-violet-500/20', dot: 'bg-violet-400' },
  short_form_video:  { label: 'Short-form Video',   badge: 'bg-ember/15 text-ember border-ember/20',               dot: 'bg-ember' },
};

const PLATFORM_STYLES: Record<string, { label: string; badge: string }> = {
  twitter:          { label: 'X / Twitter',     badge: 'bg-sky-500/10 text-sky-400 border-sky-500/20' },
  x:                { label: 'X / Twitter',     badge: 'bg-sky-500/10 text-sky-400 border-sky-500/20' },
  linkedin:         { label: 'LinkedIn',        badge: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
  facebook:         { label: 'Facebook',        badge: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' },
  instagram:        { label: 'Instagram',       badge: 'bg-pink-500/10 text-pink-400 border-pink-500/20' },
  'instagram reels':{ label: 'Instagram Reels', badge: 'bg-pink-500/10 text-pink-400 border-pink-500/20' },
  youtube:          { label: 'YouTube',         badge: 'bg-red-500/10 text-red-400 border-red-500/20' },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getPostTypeStyle(type: string) {
  return POST_TYPE_STYLES[type.toLowerCase()] ?? {
    label: type.split('_').map((s) => s.charAt(0).toUpperCase() + s.slice(1)).join(' '),
    badge: 'bg-apple-blue/15 text-apple-blue border-apple-blue/20',
    dot:   'bg-apple-blue',
  };
}

function getPlatformStyle(hint: string) {
  const key = hint.toLowerCase();
  return PLATFORM_STYLES[key] ?? { label: hint, badge: 'bg-white/[0.06] text-ink-soft border-white/[0.08]' };
}

function charCountColor(count: number, platform: string): string {
  const limit = platform.toLowerCase().includes('twitter') || platform.toLowerCase() === 'x' ? 280 : 3000;
  const pct = count / limit;
  if (pct > 0.9) return 'text-rose-400';
  if (pct > 0.7) return 'text-apple-blue';
  return 'text-ink-faint';
}

function formatDate(iso: string) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  }).format(new Date(iso));
}

// ---------------------------------------------------------------------------
// CopyButton
// ---------------------------------------------------------------------------

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  function handleCopy() {
    void navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }
  return (
    <button
      type="button"
      onClick={handleCopy}
      title="Copy to clipboard"
      className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-md border border-white/[0.06] bg-white/[0.03] text-ink-faint transition hover:border-apple-blue/30 hover:bg-apple-blue/10 hover:text-apple-blue"
    >
      {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
    </button>
  );
}

// ---------------------------------------------------------------------------
// PostCard
// ---------------------------------------------------------------------------

function PostCard({ post, index }: { post: DailyPostSuggestion; index: number }) {
  const typeStyle = getPostTypeStyle(post.post_type);
  const platformStyle = post.platform_hint ? getPlatformStyle(post.platform_hint) : null;
  const charCount = post.content.length;

  return (
    <article className="flex flex-col rounded-xl border border-white/[0.06] bg-surface-2 overflow-hidden">
      {/* Card header */}
      <div className="flex items-center justify-between gap-2 border-b border-white/[0.04] px-4 py-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-white/[0.06] text-[10px] font-bold text-ink-faint">
            {index + 1}
          </span>
          <span className={cn('inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold', typeStyle.badge)}>
            <span className={cn('h-1.5 w-1.5 rounded-full flex-shrink-0', typeStyle.dot)} />
            {typeStyle.label}
          </span>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {platformStyle && (
            <span className={cn('hidden sm:inline-flex rounded-full border px-2 py-0.5 text-[11px] font-medium', platformStyle.badge)}>
              {platformStyle.label}
            </span>
          )}
          <CopyButton text={post.content} />
        </div>
      </div>

      {/* Content body */}
      <div className="flex-1 px-4 py-4">
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink">{post.content}</p>
      </div>

      {/* Card footer */}
      <div className="flex items-center justify-between border-t border-white/[0.04] px-4 py-2.5">
        {platformStyle && (
          <span className={cn('inline-flex sm:hidden rounded-full border px-2 py-0.5 text-[11px] font-medium', platformStyle.badge)}>
            {platformStyle.label}
          </span>
        )}
        <span className={cn('ml-auto text-[11px] tabular-nums', charCountColor(charCount, post.platform_hint ?? ''))}>
          {charCount} chars
        </span>
      </div>
    </article>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function DailyPostsPage() {
  const [industry, setIndustry] = useState('SaaS');
  const [region, setRegion] = useState<string>('global');
  const [targetAudience, setTargetAudience] = useState('Founders and marketers');
  const [businessGoal, setBusinessGoal] = useState<string>('brand');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [history, setHistory] = useState<DailyPostBatch[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);

  // Load history on mount
  useEffect(() => {
    async function load() {
      setHistoryLoading(true);
      try {
        const batches = await fetchDailyPostsHistory();
        setHistory(batches);
      } catch {
        // silently ignore history fetch failure
      } finally {
        setHistoryLoading(false);
      }
    }
    void load();
  }, []);

  async function handleGenerate() {
    const trimmedIndustry = industry.trim();
    const trimmedAudience = targetAudience.trim();

    if (!trimmedIndustry) { setError('Please enter an industry.'); return; }
    if (!trimmedAudience) { setError('Please enter a target audience.'); return; }

    setLoading(true);
    setError(null);

    try {
      const batch = await generateDailyPosts({
        industry: trimmedIndustry,
        region,
        target_audience: trimmedAudience,
        business_goal: businessGoal,
      });
      setHistory((prev) => [batch, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate daily suggestions');
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageShell>
      <PageHeader
        title="Daily Posts Generator"
        description="Generate structured daily suggestions aligned to region, audience, and goal"
      />

      {/* Configuration form */}
      <section className="rounded-lg border bg-card p-5 text-card-foreground shadow-sm">
        <h2 className="mb-4 text-base font-semibold text-ink">Configuration</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-ink">Industry</label>
            <Input
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
              placeholder="e.g. SaaS, healthcare, coaching"
              disabled={loading}
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-ink">Region</label>
            <AppSelect
              value={region}
              onValueChange={setRegion}
              disabled={loading}
              options={REGIONS.map((value) => ({ value, label: value.toUpperCase() }))}
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-ink">Target audience</label>
            <Input
              value={targetAudience}
              onChange={(e) => setTargetAudience(e.target.value)}
              placeholder="e.g. founders, B2B marketers, creators"
              disabled={loading}
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-ink">Business goal</label>
            <AppSelect
              value={businessGoal}
              onValueChange={setBusinessGoal}
              disabled={loading}
              options={BUSINESS_GOALS.map((g) => ({ value: g.value, label: g.label }))}
            />
          </div>
        </div>

        <Button className="mt-4 w-full sm:w-fit" onClick={handleGenerate} disabled={loading}>
          {loading ? (
            <span className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" /> Generating...
            </span>
          ) : (
            'Generate Suggestions'
          )}
        </Button>
      </section>

      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-400">{error}</div>
      )}

      {/* History */}
      <section className="rounded-lg border bg-card text-card-foreground shadow-sm">
        <div className="flex items-center justify-between gap-3 border-b border-white/[0.06] px-5 py-4">
          <div>
            <h2 className="text-base font-semibold text-ink">Generated Batches</h2>
            <p className="text-xs text-ink-soft">Your past generations — click a row to view posts</p>
          </div>
          {history.length > 0 && (
            <span className="rounded-full bg-white/[0.06] px-3 py-1 text-xs font-semibold text-ink-soft">
              {history.length} {history.length === 1 ? 'batch' : 'batches'}
            </span>
          )}
        </div>

        <div className="p-5">
          {historyLoading ? (
            <CardListSkeleton count={3} />
          ) : history.length === 0 ? (
            <p className="text-sm text-ink-soft">No generations yet. Fill in the form above and hit Generate.</p>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {history.map((batch) => {
                const goalLabel = { brand: 'Brand Awareness', leads: 'Lead Generation', sales: 'Sales Conversion' }[batch.business_goal] ?? batch.business_goal;
                return (
                  <ListCard
                    key={batch.id}
                    title={batch.industry}
                    metadata={
                      <>
                        <span>{batch.region.toUpperCase()}</span>
                        <span>•</span>
                        <span>{batch.target_audience}</span>
                        <span>•</span>
                        <span>{formatDate(batch.created_at)}</span>
                      </>
                    }
                    tags={
                      <span className="rounded-md border border-apple-blue/20 bg-apple-blue/10 px-2 py-0.5 text-xs font-medium text-apple-blue">
                        {batch.suggestions.length} posts
                      </span>
                    }
                    footer={<span className="text-xs text-ink-soft">{goalLabel}</span>}
                    actions={[{ label: 'View details', href: `/dashboard/daily-posts/${batch.id}` }]}
                    href={`/dashboard/daily-posts/${batch.id}`}
                  />
                );
              })}
            </div>
          )}
        </div>
      </section>
    </PageShell>
  );
}
