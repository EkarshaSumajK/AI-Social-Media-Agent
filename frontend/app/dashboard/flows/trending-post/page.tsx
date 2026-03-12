'use client';

import { useEffect, useState } from 'react';
import {
  Check, Clock, Copy, ExternalLink, Flame, History, ImageIcon, Loader2, RefreshCw, Search,
  Sparkles, TrendingUp, Zap,
} from 'lucide-react';

import { ImageGeneratorModal } from '@/components/image-generator/ImageGeneratorModal';
import type { Platform } from '@/components/image-generator/types';

import Link from 'next/link';
import { PageHeader } from '@/components/page-header';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { AppSelect } from '@/components/ui/app-select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  collectTopics,
  fetchPlatformContentHistory,
  fetchSocialAccounts,
  fetchTopics,
  type FetchTopicsParams,
  generatePlatformContent,
  paraphraseContent,
  publishPlatformContent,
} from '@/lib/api';
import type { SocialAccount } from '@/lib/types';
import type { PlatformContentResponse, Topic } from '@/lib/types';
import { cn } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Platform config
// ---------------------------------------------------------------------------

const PLATFORMS = [
  {
    id: 'linkedin' as const,
    label: 'LinkedIn',
    icon: '💼',
    badge: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    preview: 'linkedin',
  },
  {
    id: 'twitter' as const,
    label: 'X / Twitter',
    icon: '𝕏',
    badge: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
    preview: 'twitter',
  },
  {
    id: 'instagram' as const,
    label: 'Instagram',
    icon: '📸',
    badge: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
    preview: 'instagram',
  },
  {
    id: 'youtube' as const,
    label: 'YouTube',
    icon: '▶',
    badge: 'bg-red-500/10 text-red-400 border-red-500/20',
    preview: 'youtube',
  },
];

const PARAPHRASE_STYLES = [
  { value: 'professional', label: 'Professional' },
  { value: 'casual', label: 'Casual' },
  { value: 'witty', label: 'Witty' },
  { value: 'formal', label: 'Formal' },
];

const PARAPHRASE_TONES = [
  { value: 'neutral', label: 'Neutral' },
  { value: 'authoritative', label: 'Authoritative' },
  { value: 'inspiring', label: 'Inspiring' },
  { value: 'conversational', label: 'Conversational' },
];

const TIME_RANGES = [
  { value: 'today' as const, label: 'Today' },
  { value: '48h' as const, label: '48h' },
  { value: 'week' as const, label: 'Week' },
  { value: 'all' as const, label: 'All' },
];

const REGIONS = [
  { value: '', label: 'All regions' },
  { value: 'global', label: 'Global' },
  { value: 'india', label: 'India' },
  { value: 'usa', label: 'USA' },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getPlatformBadge(platform: string) {
  const p = PLATFORMS.find((x) => x.id === platform.toLowerCase());
  return p ? { label: p.label, badge: p.badge } : { label: platform, badge: 'bg-white/[0.06] text-ink-soft border-white/[0.08]' };
}

function formatHistoryDate(iso: string) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  }).format(new Date(iso));
}

function prettyContentType(value: string) {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (m) => m.toUpperCase());
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      onClick={() => {
        void navigator.clipboard.writeText(text).then(() => {
          setCopied(true);
          setTimeout(() => setCopied(false), 2000);
        });
      }}
      className="flex h-7 w-7 items-center justify-center rounded-md border border-white/[0.06] bg-white/[0.03] text-ink-faint transition hover:border-apple-blue/30 hover:bg-apple-blue/10 hover:text-apple-blue"
    >
      {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
    </button>
  );
}

function HistoryRow({ item }: { item: PlatformContentResponse }) {
  const platformInfo = getPlatformBadge(item.platform);

  return (
    <Link
      href={`/dashboard/flows/trending-post/history/${item.id}`}
      className="flex items-center justify-between gap-3 rounded-lg border border-white/[0.06] bg-white/[0.02] px-4 py-3 transition-colors hover:border-apple-blue/30 hover:bg-apple-blue/5"
    >
      <div className="flex min-w-0 flex-1 items-center gap-3">
        <Clock size={14} className="flex-shrink-0 text-apple-blue/60" />
        <div className="min-w-0 text-left">
          <p className="truncate text-sm font-semibold text-ink">{item.topic}</p>
          <p className="text-[11px] text-ink-faint">{prettyContentType(item.content_type)}</p>
        </div>
      </div>
      <div className="flex flex-shrink-0 items-center gap-3">
        <span className="hidden text-[11px] text-ink-soft sm:block">
          {formatHistoryDate(item.created_at)}
        </span>
        <span className={cn('rounded-full border px-2.5 py-0.5 text-[11px] font-semibold', platformInfo.badge)}>
          {platformInfo.label}
        </span>
        <span className="text-xs font-medium text-apple-blue">View →</span>
      </div>
    </Link>
  );
}

// ---------------------------------------------------------------------------
// Platform post preview cards
// ---------------------------------------------------------------------------

function LinkedInPreview({ content }: { content: string }) {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-[#1b2433] p-4 text-sm">
      <div className="mb-3 flex items-center gap-2.5">
        <div className="h-10 w-10 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-300 font-bold text-sm">Y</div>
        <div>
          <p className="font-semibold text-white text-[13px]">You</p>
          <p className="text-[11px] text-slate-400">Content Creator • 3rd+</p>
        </div>
      </div>
      <p className="whitespace-pre-wrap leading-relaxed text-slate-200 text-[13px]">{content}</p>
      <div className="mt-3 flex items-center gap-4 border-t border-white/[0.06] pt-2.5 text-[12px] text-slate-500">
        <span>👍 Like</span><span>💬 Comment</span><span>🔁 Repost</span><span>📤 Send</span>
      </div>
    </div>
  );
}

function TwitterPreview({ content }: { content: string }) {
  return (
    <div className="rounded-xl border border-white/[0.08] bg-black p-4 text-sm">
      <div className="mb-3 flex items-center gap-2.5">
        <div className="h-10 w-10 rounded-full bg-sky-500/20 flex items-center justify-center text-sky-300 font-bold">Y</div>
        <div>
          <p className="font-semibold text-white text-[13px]">You <span className="text-slate-500 font-normal">@yourhandle</span></p>
          <p className="text-[11px] text-slate-500">Just now</p>
        </div>
      </div>
      <p className="whitespace-pre-wrap leading-relaxed text-white text-[13px]">{content}</p>
      <div className="mt-3 flex items-center gap-5 border-t border-white/[0.08] pt-2.5 text-[12px] text-slate-600">
        <span>💬 0</span><span>🔁 0</span><span>❤️ 0</span><span>📊 0</span>
      </div>
    </div>
  );
}

function InstagramPreview({ content }: { content: string }) {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-[#1a1a1a] overflow-hidden text-sm">
      <div className="flex items-center gap-2 px-3 py-2.5 border-b border-white/[0.06]">
        <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-pink-500 to-apple-blue flex items-center justify-center text-white font-bold text-xs">Y</div>
        <p className="font-semibold text-white text-[13px]">yourhandle</p>
      </div>
      <div className="aspect-square bg-gradient-to-br from-pink-500/10 to-apple-blue/10 flex items-center justify-center text-4xl">📸</div>
      <div className="p-3">
        <div className="mb-1.5 flex gap-3 text-[18px]"><span>❤️</span><span>💬</span><span>📤</span></div>
        <p className="whitespace-pre-wrap leading-relaxed text-slate-200 text-[12px]">
          <span className="font-semibold text-white">yourhandle</span>{' '}{content}
        </p>
      </div>
    </div>
  );
}

function YouTubePreview({ content }: { content: string }) {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-[#0f0f0f] overflow-hidden text-sm">
      <div className="aspect-video bg-gradient-to-br from-red-900/30 to-black flex items-center justify-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-red-600 text-white text-2xl">▶</div>
      </div>
      <div className="flex gap-3 p-3">
        <div className="h-9 w-9 flex-shrink-0 rounded-full bg-red-500/20 flex items-center justify-center text-red-400 font-bold text-sm">Y</div>
        <div>
          <p className="font-semibold text-white text-[13px] leading-snug line-clamp-2">{content.slice(0, 80)}</p>
          <p className="mt-0.5 text-[11px] text-slate-500">Your Channel • Just now</p>
        </div>
      </div>
      <div className="px-3 pb-3">
        <p className="whitespace-pre-wrap text-[12px] text-slate-400 line-clamp-3">{content}</p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Platform card (generate + preview)
// ---------------------------------------------------------------------------

interface PlatformCardProps {
  platform: typeof PLATFORMS[number];
  result: PlatformContentResponse | null;
  loading: boolean;
  error?: string;
  onParaphrase: (text: string, platform: string) => void;
  paraphrasing: boolean;
}

function PlatformCard({ platform, result, loading, error, onParaphrase, paraphrasing }: PlatformCardProps) {
  const [showParaphrase, setShowParaphrase] = useState(false);
  const [style, setStyle] = useState('professional');
  const [tone, setTone] = useState('neutral');
  const [imageOpen, setImageOpen] = useState(false);

  return (
    <div className="flex flex-col rounded-xl border border-white/[0.06] bg-surface-2 overflow-hidden">
      <div className="flex items-center justify-between gap-2 border-b border-white/[0.04] px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-base">{platform.icon}</span>
          <span className={cn('rounded-full border px-2.5 py-0.5 text-[11px] font-semibold', platform.badge)}>
            {platform.label}
          </span>
        </div>
        {result && (
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={() => setImageOpen(true)}
              title="Generate Image"
              className="flex h-7 items-center gap-1 rounded-md border border-white/[0.06] bg-white/[0.03] px-2 text-[11px] text-ink-faint transition hover:border-apple-blue/30 hover:bg-apple-blue/10 hover:text-apple-blue"
            >
              <ImageIcon size={11} /> Image
            </button>
            <button
              type="button"
              onClick={() => setShowParaphrase(!showParaphrase)}
              title="Paraphrase"
              className="flex h-7 items-center gap-1 rounded-md border border-white/[0.06] bg-white/[0.03] px-2 text-[11px] text-ink-faint transition hover:border-apple-blue/30 hover:bg-apple-blue/10 hover:text-apple-blue"
            >
              <Sparkles size={11} /> Rewrite
            </button>
            <CopyButton text={result.content} />
          </div>
        )}
      </div>

      <div className="flex-1 p-4">
        {loading ? (
          <div className="flex h-32 items-center justify-center gap-2 text-sm text-ink-soft">
            <Loader2 size={16} className="animate-spin text-apple-blue" />
            Generating for {platform.label}...
          </div>
        ) : result ? (
          <>
            {platform.id === 'linkedin' && <LinkedInPreview content={result.content} />}
            {platform.id === 'twitter' && <TwitterPreview content={result.content} />}
            {platform.id === 'instagram' && <InstagramPreview content={result.content} />}
            {platform.id === 'youtube' && <YouTubePreview content={result.content} />}
          </>
        ) : error ? (
          <div className="flex h-32 flex-col items-center justify-center gap-2 rounded-lg border border-red-500/20 bg-red-500/5 px-4 text-center">
            <p className="text-xs font-semibold text-red-400">Generation failed</p>
            <p className="text-[11px] text-red-400/70">{error}</p>
          </div>
        ) : (
          <div className="flex h-32 items-center justify-center text-sm text-ink-faint">
            Select a topic and click Generate
          </div>
        )}
      </div>

      {result && (
        <ImageGeneratorModal
          open={imageOpen}
          onOpenChange={setImageOpen}
          content={result.content}
          platform={platform.id as Platform}
          contentType={result.content_type}
        />
      )}

      {result && showParaphrase && (
        <div className="border-t border-white/[0.04] bg-apple-blue/5 px-4 pb-4 pt-3">
          <p className="mb-2.5 text-[11px] font-semibold uppercase tracking-wide text-apple-blue/70">Rewrite Style</p>
          <div className="grid grid-cols-2 gap-2 mb-3">
            <AppSelect value={style} onValueChange={setStyle} options={PARAPHRASE_STYLES} />
            <AppSelect value={tone} onValueChange={setTone} options={PARAPHRASE_TONES} />
          </div>
          <Button
            size="sm"
            className="w-full"
            onClick={() => onParaphrase(result.content, platform.id)}
            disabled={paraphrasing}
          >
            {paraphrasing ? <><Loader2 size={12} className="mr-1.5 animate-spin" /> Rewriting...</> : 'Apply Rewrite'}
          </Button>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Connect & Post section
// ---------------------------------------------------------------------------

const PUBLISH_PLATFORMS = [
  { id: 'twitter', label: 'X / Twitter', icon: '𝕏', color: 'border-sky-500/20 bg-sky-500/5' },
  { id: 'linkedin', label: 'LinkedIn', icon: '💼', color: 'border-blue-500/20 bg-blue-500/5' },
  { id: 'instagram', label: 'Instagram', icon: '📸', color: 'border-pink-500/20 bg-pink-500/5' },
  { id: 'youtube', label: 'YouTube', icon: '▶', color: 'border-red-500/20 bg-red-500/5', noPublish: true },
];

function ConnectAndPost({
  platformResults,
  socialAccounts,
  onPublish,
}: {
  platformResults: Partial<Record<string, PlatformContentResponse>>;
  socialAccounts: SocialAccount[];
  onPublish: (platform: string, contentId: number) => Promise<void>;
}) {
  const [publishing, setPublishing] = useState<string | null>(null);
  const [outcomes, setOutcomes] = useState<Record<string, 'posted' | 'failed'>>({});

  const connectedSet = new Set(socialAccounts.filter((a) => a.status === 'connected').map((a) => a.platform));

  async function handlePublish(platformId: string, contentId: number) {
    setPublishing(platformId);
    try {
      await onPublish(platformId, contentId);
      setOutcomes((prev) => ({ ...prev, [platformId]: 'posted' }));
    } catch {
      setOutcomes((prev) => ({ ...prev, [platformId]: 'failed' }));
    } finally {
      setPublishing(null);
    }
  }

  return (
    <section className="rounded-lg border bg-card text-card-foreground shadow-sm">
      <div className="border-b border-white/[0.06] px-5 py-4">
        <h2 className="text-base font-semibold text-ink">Connect & Publish</h2>
        <p className="text-xs text-ink-soft mt-0.5">Post your generated content directly to each platform</p>
      </div>
      <div className="grid gap-3 p-5 sm:grid-cols-2 lg:grid-cols-4">
        {PUBLISH_PLATFORMS.map((p) => {
          const result = platformResults[p.id];
          const connected = connectedSet.has(p.id);
          const outcome = outcomes[p.id];
          const isPublishing = publishing === p.id;

          return (
            <div key={p.id} className={cn('rounded-xl border p-4 flex flex-col items-center gap-3 text-center', p.color)}>
              <span className="text-2xl">{p.icon}</span>
              <p className="text-sm font-semibold text-ink">{p.label}</p>
              <span className={cn(
                'rounded-full border px-2.5 py-0.5 text-[10px]',
                connected ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400' : 'border-white/[0.08] bg-white/[0.04] text-ink-faint',
              )}>
                {connected ? 'Connected' : 'Not Connected'}
              </span>

              {outcome === 'posted' ? (
                <span className="flex items-center gap-1 text-[11px] text-emerald-400 font-semibold">
                  <Check size={12} /> Posted!
                </span>
              ) : outcome === 'failed' ? (
                <span className="text-[11px] text-red-400">Failed — check credentials</span>
              ) : p.noPublish ? (
                <span className="text-[10px] text-ink-faint text-center">Upload manually via YouTube Studio</span>
              ) : (
                <Button
                  size="sm"
                  className="w-full text-[11px]"
                  disabled={!result || !connected || isPublishing}
                  onClick={() => result && handlePublish(p.id, result.id)}
                >
                  {isPublishing ? <><Loader2 size={11} className="mr-1 animate-spin" /> Posting...</> : 'Post Now'}
                </Button>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function TrendingPostFlowPage() {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [topicsLoading, setTopicsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTopic, setSelectedTopic] = useState<Topic | null>(null);
  const [collectingWeb, setCollectingWeb] = useState(false);
  const [activity, setActivity] = useState<string | null>(null);

  const [filters, setFilters] = useState<FetchTopicsParams>({
    since: 'week',
    q: undefined,
    region: undefined,
  });

  const [platformResults, setPlatformResults] = useState<Partial<Record<string, PlatformContentResponse>>>({});
  const [platformErrors, setPlatformErrors] = useState<Partial<Record<string, string>>>({});
  const [generatingPlatforms, setGeneratingPlatforms] = useState<Set<string>>(new Set());
  const [generating, setGenerating] = useState(false);
  const [paraphrasingPlatform, setParaphrasingPlatform] = useState<string | null>(null);

  const [socialAccounts, setSocialAccounts] = useState<SocialAccount[]>([]);

  const [history, setHistory] = useState<PlatformContentResponse[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyPage, setHistoryPage] = useState(1);

  const HISTORY_PAGE_SIZE = 10;
  const historyTotalPages = Math.max(1, Math.ceil(history.length / HISTORY_PAGE_SIZE));
  const historyPaginated = history.slice(
    (historyPage - 1) * HISTORY_PAGE_SIZE,
    historyPage * HISTORY_PAGE_SIZE,
  );

  const fetchParams: FetchTopicsParams = {
    since: filters.since ?? 'week',
    q: filters.q || undefined,
    region: filters.region || undefined,
    is_trending: true,
  };

  // Load DB topics when filters change
  useEffect(() => {
    async function load() {
      setTopicsLoading(true);
      try {
        const data = await fetchTopics(fetchParams);
        setTopics(data);
      } catch {
        // ignore
      } finally {
        setTopicsLoading(false);
      }
    }
    void load();
  }, [filters.since, filters.q, filters.region]);

  async function loadHistory() {
    setHistoryLoading(true);
    try {
      const data = await fetchPlatformContentHistory();
      setHistory(data);
      setHistoryPage(1);
    } catch {
      // ignore
    } finally {
      setHistoryLoading(false);
    }
  }

  useEffect(() => {
    void loadHistory();
    fetchSocialAccounts().then(setSocialAccounts).catch(() => {});
  }, []);

  // Client-side filter for instant search while typing (searchQuery)
  const filtered = topics.filter((t) => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return true;
    return (
      t.title.toLowerCase().includes(q) ||
      (t.summary ?? '').toLowerCase().includes(q) ||
      (t.x_trend_phrase ?? '').toLowerCase().includes(q) ||
      (t.topic_category ?? '').toLowerCase().includes(q)
    );
  });

  async function handleSearchWeb() {
    setCollectingWeb(true);
    setActivity(null);
    try {
      const query = searchQuery.trim() || undefined;
      const res = await collectTopics(query);
      setActivity(`Found ${res.x_topics_found} X topics, stored ${res.stored} new. ${res.fetched} articles fetched.`);
      const data = await fetchTopics(fetchParams);
      setTopics(data);
    } catch (err) {
      setActivity(err instanceof Error ? err.message : 'Web search failed');
    } finally {
      setCollectingWeb(false);
    }
  }

  async function handleGenerate() {
    if (!selectedTopic) return;
    setGenerating(true);
    setPlatformResults({});
    setPlatformErrors({});
    const platforms = PLATFORMS.map((p) => p.id);
    setGeneratingPlatforms(new Set(platforms));

    await Promise.allSettled(
      platforms.map(async (platform) => {
        try {
          const res = await generatePlatformContent({
            topic: selectedTopic.title,
            platform: platform as 'linkedin' | 'instagram' | 'twitter' | 'youtube',
            content_type: platform === 'youtube' ? 'video_outline' : platform === 'twitter' ? 'thread' : 'authority_post',
          });
          setPlatformResults((prev) => ({ ...prev, [platform]: res }));
        } catch (err) {
          setPlatformErrors((prev) => ({
            ...prev,
            [platform]: err instanceof Error ? err.message : 'Generation failed',
          }));
        } finally {
          setGeneratingPlatforms((prev) => {
            const next = new Set(prev);
            next.delete(platform);
            return next;
          });
        }
      }),
    );

    setGenerating(false);
    void loadHistory();
  }

  async function handleParaphrase(text: string, platform: string) {
    setParaphrasingPlatform(platform);
    try {
      const res = await paraphraseContent(text, 'professional', 'neutral');
      setPlatformResults((prev) => ({
        ...prev,
        [platform]: { ...(prev[platform] as PlatformContentResponse), content: res.paraphrased },
      }));
    } finally {
      setParaphrasingPlatform(null);
    }
  }

  async function handlePublish(platform: string, contentId: number) {
    await publishPlatformContent(contentId);
  }

  const hasContent = Object.keys(platformResults).length > 0;

  return (
    <div className="flex flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
      <PageHeader
        title="Trending → Post All Platforms"
        description="Pick a trending topic and generate ready-to-post content for every platform in one click"
        eyebrow="Flow"
      />

      {/* Step 1: Topic Picker */}
      <section className="rounded-lg border bg-card text-card-foreground shadow-sm">
        <div className="border-b border-white/[0.06] px-5 py-4 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-apple-blue/15 text-[11px] font-bold text-apple-blue">1</span>
              <h2 className="text-base font-semibold text-ink">Pick a Trending Topic</h2>
            </div>
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <div className="relative flex-1 sm:w-64">
                <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint" />
                <Input
                  className="h-8 pl-8 text-sm"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') void handleSearchWeb(); }}
                  placeholder="Search topics or enter query for web..."
                />
              </div>
              <Button size="sm" variant="outline" onClick={handleSearchWeb} disabled={collectingWeb} className="flex-shrink-0">
                {collectingWeb ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />}
                <span className="hidden sm:inline ml-1.5">Search Web</span>
              </Button>
            </div>
          </div>

          {/* Filters */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-medium text-ink-faint uppercase tracking-wider">Time</span>
              <div className="flex rounded-lg border border-white/[0.06] bg-white/[0.03] p-0.5">
                {TIME_RANGES.map((r) => (
                  <button
                    key={r.value}
                    type="button"
                    onClick={() => setFilters((f) => ({ ...f, since: r.value }))}
                    className={cn(
                      'px-2.5 py-1 text-[11px] font-medium rounded-md transition',
                      filters.since === r.value ? 'bg-apple-blue/15 text-apple-blue' : 'text-ink-faint hover:text-ink',
                    )}
                  >
                    {r.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-medium text-ink-faint uppercase tracking-wider">Region</span>
              <select
                value={filters.region ?? ''}
                onChange={(e) => setFilters((f) => ({ ...f, region: e.target.value || undefined }))}
                className="h-7 rounded-md border border-white/[0.08] bg-surface-2 px-2.5 text-[11px] text-ink focus:border-apple-blue/30 focus:outline-none"
              >
                {REGIONS.map((r) => (
                  <option key={r.value || 'all'} value={r.value}>{r.label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {activity && (
          <div className="mx-5 mt-4 rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-400">
            {activity}
          </div>
        )}

        <div className="p-5">
          {topicsLoading ? (
            <div className="flex items-center gap-2 py-8 text-sm text-ink-soft">
              <Loader2 size={14} className="animate-spin" /> Loading topics...
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-8 text-center">
              <TrendingUp size={32} className="text-ink-faint" />
              <p className="text-sm text-ink-soft">No topics yet. Click "Search Web" to fetch trending topics.</p>
            </div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {filtered.slice(0, 12).map((topic) => {
                const isSelected = selectedTopic?.id === topic.id;
                const trust = topic.trust_score ?? 0;
                const trustColor =
                  trust >= 80 ? 'bg-emerald-400' : trust >= 60 ? 'bg-apple-blue-500' : 'bg-red-400';
                const trustLabel =
                  trust >= 80 ? 'text-emerald-400' : trust >= 60 ? 'text-apple-blue-500' : 'text-red-400';
                return (
                  <button
                    key={topic.id}
                    type="button"
                    onClick={() => { setSelectedTopic(topic); setPlatformResults({}); }}
                    className={cn(
                      'group relative flex flex-col gap-3 rounded-xl border p-4 text-left transition-all duration-150',
                      isSelected
                        ? 'border-apple-blue/50 bg-apple-blue/[0.06] shadow-[0_0_0_3px_rgba(34,197,94,0.12)]'
                        : 'border-white/[0.06] bg-surface-2 hover:border-white/[0.12] hover:bg-white/[0.04]',
                    )}
                  >
                    {/* Selected checkmark */}
                    <div className={cn(
                      'absolute right-3 top-3 flex h-5 w-5 items-center justify-center rounded-full border transition',
                      isSelected
                        ? 'border-apple-blue bg-apple-blue text-white'
                        : 'border-white/[0.1] bg-transparent text-transparent group-hover:border-white/[0.2]',
                    )}>
                      <Check size={11} strokeWidth={2.5} />
                    </div>

                    {/* Top badges */}
                    <div className="flex flex-wrap items-center gap-1.5">
                      {topic.is_trending && (
                        <span className="inline-flex items-center gap-1 rounded-full border border-apple-blue/25 bg-apple-blue/10 px-2 py-0.5 text-[10px] font-semibold text-apple-blue">
                          <Flame size={9} className="text-apple-blue" /> Trending
                        </span>
                      )}
                      {topic.x_trend_phrase && (
                        <span className="inline-flex items-center gap-1 rounded-full border border-sky-500/20 bg-sky-500/10 px-2 py-0.5 text-[10px] font-medium text-sky-400">
                          𝕏 {topic.x_trend_phrase}
                        </span>
                      )}
                      {topic.topic_category && (
                        <span className="rounded-full border border-white/[0.06] bg-white/[0.04] px-2 py-0.5 text-[10px] text-ink-faint capitalize">
                          {topic.topic_category.replace(/_/g, ' ')}
                        </span>
                      )}
                    </div>

                    {/* Title */}
                    <p className="pr-5 text-[13px] font-semibold leading-snug text-ink line-clamp-2">
                      {topic.title}
                    </p>

                    {/* Summary */}
                    {topic.summary && (
                      <p className="line-clamp-2 text-[11px] leading-relaxed text-ink-faint">
                        {topic.summary}
                      </p>
                    )}

                    {/* Trust score bar */}
                    <div className="flex items-center gap-2">
                      <div className="h-1 flex-1 overflow-hidden rounded-full bg-white/[0.06]">
                        <div
                          className={cn('h-full rounded-full transition-all', trustColor)}
                          style={{ width: `${trust}%` }}
                        />
                      </div>
                      <span className={cn('text-[10px] font-semibold tabular-nums', trustLabel)}>
                        {trust}
                      </span>
                    </div>

                    {/* Footer row */}
                    <div className="flex items-center justify-between gap-2 text-[10px]">
                      <div className="flex items-center gap-2 min-w-0">
                        {topic.source_name && (
                          <span className="truncate text-ink-faint">{topic.source_name}</span>
                        )}
                        {topic.region && (
                          <span className="rounded border border-white/[0.06] bg-white/[0.03] px-1.5 py-0.5 text-ink-faint">
                            {topic.region}
                          </span>
                        )}
                      </div>
                      {topic.source_url && (
                        <a
                          href={topic.source_url}
                          target="_blank"
                          rel="noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="inline-flex flex-shrink-0 items-center gap-0.5 text-apple-blue/50 transition hover:text-apple-blue"
                        >
                          <ExternalLink size={10} />
                        </a>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </section>

      {/* Step 2: Generate */}
      {selectedTopic && (
        <section className="rounded-lg border bg-card text-card-foreground shadow-sm p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-apple-blue/15 text-[11px] font-bold text-apple-blue">2</span>
              <div>
                <p className="text-sm font-semibold text-ink">{selectedTopic.title}</p>
                <p className="text-xs text-ink-soft">Selected topic — generate for all 4 platforms</p>
              </div>
            </div>
            <Button onClick={handleGenerate} disabled={generating} className="min-w-[180px]">
              {generating ? (
                <><Loader2 size={14} className="mr-2 animate-spin" /> Generating...</>
              ) : (
                <><Zap size={14} className="mr-2" /> Generate All Platforms</>
              )}
            </Button>
          </div>
        </section>
      )}

      {/* Step 3: Platform previews */}
      {(hasContent || generatingPlatforms.size > 0) && (
        <section className="rounded-lg border bg-card text-card-foreground shadow-sm">
          <div className="border-b border-white/[0.06] px-5 py-4 flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-apple-blue/15 text-[11px] font-bold text-apple-blue">3</span>
            <h2 className="text-base font-semibold text-ink">Preview & Refine</h2>
          </div>

          <Tabs defaultValue="linkedin" className="p-5">
            <TabsList className="mb-5 h-9 w-full justify-start gap-1 rounded-lg bg-white/[0.04] p-1">
              {PLATFORMS.map((p) => (
                <TabsTrigger
                  key={p.id}
                  value={p.id}
                  className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[12px] data-[state=active]:bg-white/[0.08] data-[state=active]:text-ink"
                >
                  <span>{p.icon}</span>
                  <span className="hidden sm:inline">{p.label}</span>
                  {generatingPlatforms.has(p.id) && <Loader2 size={11} className="animate-spin text-apple-blue" />}
                  {platformResults[p.id] && !generatingPlatforms.has(p.id) && (
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                  )}
                </TabsTrigger>
              ))}
            </TabsList>

            {PLATFORMS.map((p) => (
              <TabsContent key={p.id} value={p.id}>
                <PlatformCard
                  platform={p}
                  result={platformResults[p.id] ?? null}
                  loading={generatingPlatforms.has(p.id)}
                  error={platformErrors[p.id]}
                  onParaphrase={handleParaphrase}
                  paraphrasing={paraphrasingPlatform === p.id}
                />
              </TabsContent>
            ))}
          </Tabs>
        </section>
      )}

      {/* Step 4: Connect & Post */}
      {hasContent && (
        <ConnectAndPost
          platformResults={platformResults}
          socialAccounts={socialAccounts}
          onPublish={handlePublish}
        />
      )}

      {/* Previous Generated Posts */}
      <section className="rounded-lg border bg-card text-card-foreground shadow-sm">
        <div className="border-b border-white/[0.06] px-5 py-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <History size={18} className="text-apple-blue/80" />
            <h2 className="text-base font-semibold text-ink">Previous Generated Posts</h2>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => void loadHistory()}
            disabled={historyLoading}
            className="text-[11px]"
          >
            {historyLoading ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />}
            <span className="ml-1.5">Refresh</span>
          </Button>
        </div>
        <div className="p-5">
          {historyLoading ? (
            <div className="flex items-center gap-2 py-8 text-sm text-ink-soft">
              <Loader2 size={14} className="animate-spin" /> Loading history...
            </div>
          ) : history.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-8 text-center">
              <History size={32} className="text-ink-faint" />
              <p className="text-sm text-ink-soft">No generated posts yet. Pick a topic and click Generate.</p>
            </div>
          ) : (
            <>
              <div className="space-y-2">
                {historyPaginated.map((item) => (
                  <HistoryRow key={item.id} item={item} />
                ))}
              </div>
              {history.length > HISTORY_PAGE_SIZE && (
                <div className="mt-4 flex items-center justify-between gap-3 border-t border-white/[0.06] pt-4">
                  <p className="text-xs text-ink-faint">
                    Showing {(historyPage - 1) * HISTORY_PAGE_SIZE + 1}–{Math.min(historyPage * HISTORY_PAGE_SIZE, history.length)} of {history.length}
                  </p>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setHistoryPage((p) => Math.max(1, p - 1))}
                      disabled={historyPage <= 1}
                      className="h-8 px-2.5 text-xs"
                    >
                      Previous
                    </Button>
                    <span className="px-2 text-xs text-ink-soft">
                      Page {historyPage} of {historyTotalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setHistoryPage((p) => Math.min(historyTotalPages, p + 1))}
                      disabled={historyPage >= historyTotalPages}
                      className="h-8 px-2.5 text-xs"
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </section>
    </div>
  );
}
