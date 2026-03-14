'use client';

import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';

import { ListCard } from '@/components/list-card';
import { PageHeader } from '@/components/page-header';
import { PageShell } from '@/components/page-shell';
import { CardListSkeleton } from '@/components/skeletons';
import { AppSelect } from '@/components/ui/app-select';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { fetchPlatformContentHistory, generatePlatformContent } from '@/lib/api';
import type { PlatformContentResponse, PlatformContentTarget } from '@/lib/types';
import { cn } from '@/lib/utils';

const TARGET_PLATFORMS: { value: PlatformContentTarget; label: string; badge: string }[] = [
  { value: 'linkedin',  label: 'LinkedIn',     badge: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
  { value: 'instagram', label: 'Instagram',    badge: 'bg-pink-500/10 text-pink-400 border-pink-500/20' },
  { value: 'twitter',   label: 'X (Twitter)',  badge: 'bg-sky-500/10 text-sky-400 border-sky-500/20' },
  { value: 'youtube',   label: 'YouTube',      badge: 'bg-red-500/10 text-red-400 border-red-500/20' },
];

const CONTENT_TYPES = [
  { value: 'authority_post', label: 'Authority Post' },
  { value: 'story_post',     label: 'Story Post' },
  { value: 'thread',         label: 'Thread' },
  { value: 'reel_script',    label: 'Reel Script' },
  { value: 'video_outline',  label: 'Video Outline' },
  { value: 'poll_post',      label: 'Poll Post' },
] as const;

function getPlatformBadge(platform: string) {
  return TARGET_PLATFORMS.find((p) => p.value === platform.toLowerCase()) ?? {
    label: platform,
    badge: 'bg-white/[0.06] text-ink-soft border-white/[0.08]',
  };
}

function prettyKey(value: string) {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (m) => m.toUpperCase());
}

function formatDate(iso: string) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  }).format(new Date(iso));
}

export default function PlatformContentPage() {
  const [topic, setTopic] = useState('AI productivity for founders');
  const [platform, setPlatform] = useState<PlatformContentTarget>('linkedin');
  const [contentType, setContentType] = useState<string>('authority_post');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [history, setHistory] = useState<PlatformContentResponse[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setHistoryLoading(true);
      try {
        const data = await fetchPlatformContentHistory();
        setHistory(data);
      } catch {
        // silently ignore
      } finally {
        setHistoryLoading(false);
      }
    }
    void load();
  }, []);

  async function handleGenerate() {
    const trimmedTopic = topic.trim();
    if (!trimmedTopic) { setError('Please enter a topic.'); return; }
    if (!contentType.trim()) { setError('Please choose a content type.'); return; }

    setLoading(true);
    setError(null);

    try {
      const res = await generatePlatformContent({
        topic: trimmedTopic,
        platform,
        content_type: contentType,
      });
      setHistory((prev) => [res, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate platform content');
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageShell>
      <PageHeader
        title="Platform Generator"
        description="Generate platform-optimized content using backend platform/content-type contracts"
      />

      <section className="rounded-lg border bg-card p-5 text-card-foreground shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-ink">Configuration</h2>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="md:col-span-2">
            <label className="mb-1.5 block text-sm font-medium text-ink">Topic</label>
            <Input
              value={topic}
              onChange={(event) => setTopic(event.target.value)}
              placeholder="e.g. building trust with AI-generated content"
              disabled={loading}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-ink">Target platform</label>
            <AppSelect
              value={platform}
              onValueChange={(value) => setPlatform(value as PlatformContentTarget)}
              disabled={loading}
              options={TARGET_PLATFORMS.map((item) => ({ value: item.value, label: item.label }))}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-ink">Content type</label>
            <AppSelect
              value={contentType}
              onValueChange={setContentType}
              disabled={loading}
              options={CONTENT_TYPES.map((item) => ({ value: item.value, label: item.label }))}
            />
          </div>
        </div>

        <Button className="mt-4 w-full sm:w-fit" onClick={handleGenerate} disabled={loading}>
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating...
            </>
          ) : (
            'Generate Platform Content'
          )}
        </Button>
      </section>

      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* History */}
      <section className="rounded-lg border bg-card text-card-foreground shadow-sm">
        <div className="flex items-center justify-between gap-3 border-b border-white/[0.06] px-5 py-4">
          <div>
            <h2 className="text-base font-semibold text-ink">History</h2>
            <p className="text-xs text-ink-soft">Your past generations — click to view content</p>
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
            <p className="text-sm text-ink-soft">No generations yet. Fill in the form above and hit Generate.</p>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {history.map((item) => {
                const platformInfo = getPlatformBadge(item.platform);
                return (
                  <ListCard
                    key={item.id}
                    title={item.topic}
                    metadata={
                      <>
                        <span>{prettyKey(item.content_type)}</span>
                        <span>•</span>
                        <span>{formatDate(item.created_at)}</span>
                      </>
                    }
                    tags={
                      <span className={cn('rounded-md border px-2 py-0.5 text-xs font-medium', platformInfo.badge)}>
                        {platformInfo.label}
                      </span>
                    }
                    actions={[{ label: 'View details', href: `/dashboard/platform-content/history/${item.id}` }]}
                    href={`/dashboard/platform-content/history/${item.id}`}
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
