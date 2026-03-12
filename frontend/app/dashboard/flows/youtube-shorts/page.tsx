'use client';

import { useEffect, useState } from 'react';
import { Check, Copy, Loader2, Tag, Youtube } from 'lucide-react';

import { ListCard } from '@/components/list-card';
import { PageHeader } from '@/components/page-header';
import { PageShell } from '@/components/page-shell';
import { CardListSkeleton } from '@/components/skeletons';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { fetchYoutubeShortsHistory, generateYoutubeShort } from '@/lib/api';
import type { YoutubeShortResponse } from '@/lib/types';
import { cn } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(iso: string) {
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(iso));
}

function CopyButton({ text, label }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      onClick={() => { void navigator.clipboard.writeText(text).then(() => { setCopied(true); setTimeout(() => setCopied(false), 2000); }); }}
      className={cn(
        'flex items-center gap-1.5 rounded-md border px-2 py-1 text-[11px] transition',
        copied
          ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
          : 'border-white/[0.06] bg-white/[0.03] text-ink-faint hover:border-apple-blue/30 hover:bg-apple-blue/10 hover:text-apple-blue',
      )}
    >
      {copied ? <Check size={11} /> : <Copy size={11} />}
      {label && <span>{copied ? 'Copied!' : label}</span>}
    </button>
  );
}

// ---------------------------------------------------------------------------
// Output cards
// ---------------------------------------------------------------------------

function OutputSection({ title, children, copyText }: { title: string; children: React.ReactNode; copyText?: string }) {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-surface-2 overflow-hidden">
      <div className="flex items-center justify-between border-b border-white/[0.04] px-4 py-3">
        <p className="text-[11px] font-semibold uppercase tracking-[0.15em] text-ink-soft">{title}</p>
        {copyText && <CopyButton text={copyText} />}
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

function ShortOutput({ short }: { short: YoutubeShortResponse }) {
  return (
    <div className="flex flex-col gap-4">
      {/* Hook */}
      <OutputSection title="Hook — Opening Line" copyText={short.hook}>
        <p className="text-base font-semibold leading-snug text-apple-blue">&ldquo;{short.hook}&rdquo;</p>
      </OutputSection>

      {/* Script */}
      <OutputSection
        title="Script"
        copyText={[
          short.script.intro,
          ...(short.script.main_points || []).map((mp: { title: string; content: string }) => `${mp.title}:\n${mp.content}`),
          short.script.cta,
        ].join('\n\n')}
      >
        <div className="flex flex-col gap-3">
          <div>
            <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-ocean">Intro</p>
            <p className="text-sm leading-relaxed text-ink">{short.script.intro}</p>
          </div>
          {(short.script.main_points || []).map((mp: { title: string; content: string }, i: number) => (
            <div key={i}>
              <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-moss">Point {i + 1} · {mp.title}</p>
              <p className="text-sm leading-relaxed text-ink">{mp.content}</p>
            </div>
          ))}
          <div>
            <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-ember">CTA</p>
            <p className="text-sm leading-relaxed text-ink">{short.script.cta}</p>
          </div>
        </div>
      </OutputSection>

      {/* Titles */}
      <OutputSection title="Title Options">
        <div className="flex flex-col gap-2">
          {(short.titles || []).map((title: string, i: number) => (
            <div key={i} className="flex items-center justify-between gap-2 rounded-lg bg-white/[0.03] px-3 py-2.5">
              <p className="text-sm font-medium text-ink flex-1">{title}</p>
              <CopyButton text={title} />
            </div>
          ))}
        </div>
      </OutputSection>

      {/* Description */}
      <OutputSection title="YouTube Description" copyText={short.description}>
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink">{short.description}</p>
      </OutputSection>

      {/* Tags */}
      <OutputSection title="Tags" copyText={short.tags.join(', ')}>
        <div className="flex flex-wrap gap-2">
          {(short.tags || []).map((tag: string, i: number) => (
            <span key={i} className="flex items-center gap-1 rounded-full border border-white/[0.06] bg-white/[0.03] px-2.5 py-1 text-[11px] text-ink-soft">
              <Tag size={9} />
              {tag}
            </span>
          ))}
        </div>
        <button
          type="button"
          onClick={() => { void navigator.clipboard.writeText(short.tags.join(', ')); }}
          className="mt-3 text-[11px] text-apple-blue/70 hover:text-apple-blue hover:underline"
        >
          Copy all tags
        </button>
      </OutputSection>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function YouTubeShortsFlowPage() {
  const [topic, setTopic] = useState('');
  const [audience, setAudience] = useState('');
  const [duration, setDuration] = useState(60);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [history, setHistory] = useState<YoutubeShortResponse[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setHistoryLoading(true);
      try {
        const data = await fetchYoutubeShortsHistory();
        setHistory(data);
      } catch {
        // ignore
      } finally {
        setHistoryLoading(false);
      }
    }
    void load();
  }, []);

  async function handleGenerate() {
    if (!topic.trim()) { setError('Please enter a topic.'); return; }
    setLoading(true);
    setError(null);
    try {
      const res = await generateYoutubeShort({
        topic: topic.trim(),
        target_audience: audience.trim() || undefined,
        duration,
      });
      setHistory((prev) => [res, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate');
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageShell>
      <PageHeader
        title="YouTube Shorts Creator"
        description="Generate a complete YouTube Short: hook, script, titles, description, and tags"
        eyebrow="Flow"
      />

      <section className="rounded-lg border bg-card p-5 text-card-foreground shadow-sm">
        <div className="mb-4 flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-red-500/15 text-[11px] font-bold text-red-400">▶</span>
          <h2 className="text-base font-semibold text-ink">Short Brief</h2>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="md:col-span-2">
            <label className="mb-1.5 block text-sm font-medium text-ink">Topic *</label>
            <Input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. 5 AI tools that will replace your entire marketing team"
              disabled={loading}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-ink">Target Audience</label>
            <Input
              value={audience}
              onChange={(e) => setAudience(e.target.value)}
              placeholder="e.g. SaaS founders, marketers"
              disabled={loading}
            />
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <label className="text-sm font-medium text-ink">Duration</label>
              <span className="text-sm font-semibold text-red-400">{duration}s</span>
            </div>

            {/* Slider */}
            <input
              type="range"
              min={15}
              max={90}
              step={5}
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              disabled={loading}
              className="h-1.5 w-full cursor-pointer appearance-none rounded-full bg-white/[0.08] accent-red-500 disabled:opacity-50"
            />
            <div className="mt-1 flex justify-between text-[10px] text-ink-faint">
              <span>15s</span>
              <span>90s</span>
            </div>

            {/* Quick presets */}
            <div className="mt-3 flex flex-wrap gap-1.5">
              {[15, 30, 45, 60, 75, 90].map((d) => (
                <button
                  key={d}
                  type="button"
                  disabled={loading}
                  onClick={() => setDuration(d)}
                  className={cn(
                    'rounded-full border px-2.5 py-0.5 text-[11px] font-medium transition',
                    duration === d
                      ? 'border-red-500/40 bg-red-500/10 text-red-400'
                      : 'border-white/[0.06] bg-white/[0.02] text-ink-faint hover:border-red-500/30 hover:text-ink',
                  )}
                >
                  {d}s
                </button>
              ))}
            </div>
          </div>
        </div>

        <Button className="mt-4 w-full sm:w-fit" onClick={handleGenerate} disabled={loading}>
          {loading ? (
            <><Loader2 size={14} className="mr-2 animate-spin" /> Generating...</>
          ) : (
            <><Youtube size={14} className="mr-2" /> Generate Short</>
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
            <h2 className="text-base font-semibold text-ink">Your Shorts</h2>
            <p className="text-xs text-ink-soft">Click to view the full script, titles, and tags</p>
          </div>
          {history.length > 0 && (
            <span className="rounded-full bg-white/[0.06] px-3 py-1 text-xs font-semibold text-ink-soft">
              {history.length}
            </span>
          )}
        </div>

        <div className="p-5">
          {historyLoading ? (
            <CardListSkeleton count={3} />
          ) : history.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-8 text-center">
              <Youtube size={32} className="text-ink-faint" />
              <p className="text-sm text-ink-soft">No Shorts yet. Enter a topic above and generate one.</p>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {history.map((item) => (
                <ListCard
                  key={item.id}
                  title={item.topic}
                  metadata={
                    <>
                      <span>{item.duration}s</span>
                      <span>•</span>
                      <span>{item.target_audience ?? 'General audience'}</span>
                      <span>•</span>
                      <span>{formatDate(item.created_at)}</span>
                    </>
                  }
                  tags={
                    <span className="rounded-md border border-red-500/20 bg-red-500/10 px-2 py-0.5 text-xs font-medium text-red-400">
                      {item.titles?.[0]?.slice(0, 30) ?? 'Short'}…
                    </span>
                  }
                  actions={[{ label: 'View details', href: `/dashboard/flows/youtube-shorts/history/${item.id}` }]}
                  href={`/dashboard/flows/youtube-shorts/history/${item.id}`}
                />
              ))}
            </div>
          )}
        </div>
      </section>
    </PageShell>
  );
}
