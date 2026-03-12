'use client';

import { useEffect, useState } from 'react';
import {
  Check, ChevronDown, ChevronUp, Copy, Globe, Hash, Loader2, MapPin, Sparkles, TrendingUp,
} from 'lucide-react';

import { PageHeader } from '@/components/page-header';
import { AppSelect } from '@/components/ui/app-select';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  fetchRegionalHashtags,
  fetchRegionalHistory,
  fetchRegionalTrendingTopics,
  localiseContent,
} from '@/lib/api';
import type {
  LocaliseResponse,
  RegionalHashtagResponse,
  RegionalHistoryItem,
  RegionalTrendingResponse,
} from '@/lib/types';
import { cn } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const REGIONS = [
  { value: 'india', label: '🇮🇳 India' },
  { value: 'usa', label: '🇺🇸 USA' },
  { value: 'uk', label: '🇬🇧 United Kingdom' },
  { value: 'uae', label: '🇦🇪 UAE / Gulf' },
  { value: 'canada', label: '🇨🇦 Canada' },
  { value: 'australia', label: '🇦🇺 Australia' },
  { value: 'singapore', label: '🇸🇬 Singapore' },
  { value: 'germany', label: '🇩🇪 Germany' },
  { value: 'france', label: '🇫🇷 France' },
  { value: 'global', label: '🌍 Global' },
];

const INDUSTRIES = [
  { value: 'technology', label: 'Technology' },
  { value: 'marketing', label: 'Marketing' },
  { value: 'finance', label: 'Finance' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'education', label: 'Education' },
  { value: 'retail', label: 'Retail / E-Commerce' },
  { value: 'real_estate', label: 'Real Estate' },
  { value: 'startup', label: 'Startup / VC' },
  { value: 'creator_economy', label: 'Creator Economy' },
  { value: 'ai', label: 'AI / ML' },
  { value: 'consulting', label: 'Consulting' },
  { value: 'legal', label: 'Legal' },
  { value: 'other', label: 'Other' },
];

const LANGUAGE_STYLES = [
  { value: 'english', label: 'English (Standard)' },
  { value: 'english_casual', label: 'English (Casual / Gen Z)' },
  { value: 'hinglish', label: 'Hinglish (India)' },
  { value: 'hindi', label: 'Hindi' },
  { value: 'arabic', label: 'Arabic' },
  { value: 'german', label: 'German' },
  { value: 'french', label: 'French' },
];

const SOCIAL_PLATFORMS = [
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'twitter', label: 'X / Twitter' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'youtube', label: 'YouTube' },
];

const TIME_FRAMES = [
  { value: 'today', label: 'Today' },
  { value: 'this week', label: 'This Week' },
  { value: 'this month', label: 'This Month' },
];

const URGENCY_COLORS: Record<string, string> = {
  high: 'border-red-500/20 bg-red-500/10 text-red-400',
  medium: 'border-apple-blue/20 bg-apple-blue/10 text-apple-blue',
  low: 'border-emerald-500/20 bg-emerald-500/10 text-emerald-400',
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      onClick={() => {
        void navigator.clipboard.writeText(text).then(() => {
          setCopied(true);
          setTimeout(() => setCopied(false), 1800);
        });
      }}
      className="flex h-7 w-7 items-center justify-center rounded-md border border-white/[0.06] bg-white/[0.03] text-ink-faint transition hover:border-apple-blue/30 hover:bg-apple-blue/10 hover:text-apple-blue"
    >
      {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
    </button>
  );
}

function SectionCard({ title, children, action }: { title: string; children: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-surface-2 overflow-hidden">
      <div className="flex items-center justify-between border-b border-white/[0.04] px-4 py-3">
        <p className="text-[11px] font-semibold uppercase tracking-[0.15em] text-ink-soft">{title}</p>
        {action}
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab: Localise Content
// ---------------------------------------------------------------------------

function LocaliseTab() {
  const [content, setContent] = useState('');
  const [region, setRegion] = useState('india');
  const [langStyle, setLangStyle] = useState('english');
  const [result, setResult] = useState<LocaliseResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleLocalise() {
    if (!content.trim()) { setError('Please enter content to localise.'); return; }
    setLoading(true);
    setError(null);
    try {
      const res = await localiseContent({
        content: content.trim(),
        region,
        language_style: langStyle,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Localisation failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="grid gap-4 lg:grid-cols-[1fr_200px_200px]">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-ink">Original Content *</label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Paste your LinkedIn post, tweet, or any content here…"
            rows={6}
            disabled={loading}
            className="w-full resize-none rounded-lg border border-white/[0.08] bg-surface-2 px-3 py-2.5 text-sm text-ink placeholder:text-ink-faint focus:border-apple-blue/40 focus:outline-none disabled:opacity-50"
          />
        </div>
        <div className="flex flex-col gap-3">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-ink">Target Region</label>
            <AppSelect value={region} onValueChange={setRegion} options={REGIONS} disabled={loading} />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-ink">Language Style</label>
            <AppSelect value={langStyle} onValueChange={setLangStyle} options={LANGUAGE_STYLES} disabled={loading} />
          </div>
        </div>
      </div>

      {error && <p className="rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-400">{error}</p>}

      <Button onClick={() => void handleLocalise()} disabled={loading} className="w-full sm:w-fit">
        {loading
          ? <><Loader2 size={14} className="mr-2 animate-spin" /> Localising…</>
          : <><Globe size={14} className="mr-2" /> Localise Content</>}
      </Button>

      {result && (
        <SectionCard
          title={`Localised for ${result.region} · ${result.language_style}`}
          action={<CopyButton text={result.localised_content} />}
        >
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink">{result.localised_content}</p>
        </SectionCard>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab: Regional Trending Topics
// ---------------------------------------------------------------------------

function TrendingTopicsTab() {
  const [region, setRegion] = useState('india');
  const [industry, setIndustry] = useState('technology');
  const [timeFrame, setTimeFrame] = useState('this week');
  const [result, setResult] = useState<RegionalTrendingResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFetch() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchRegionalTrendingTopics({ region, industry, time_frame: timeFrame });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch trending topics');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="grid gap-3 sm:grid-cols-3">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-ink">Region</label>
          <AppSelect value={region} onValueChange={setRegion} options={REGIONS} disabled={loading} />
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-ink">Industry</label>
          <AppSelect value={industry} onValueChange={setIndustry} options={INDUSTRIES} disabled={loading} />
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-ink">Time Frame</label>
          <AppSelect value={timeFrame} onValueChange={setTimeFrame} options={TIME_FRAMES} disabled={loading} />
        </div>
      </div>

      {error && <p className="rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-400">{error}</p>}

      <Button onClick={() => void handleFetch()} disabled={loading} className="w-full sm:w-fit">
        {loading
          ? <><Loader2 size={14} className="mr-2 animate-spin" /> Analysing…</>
          : <><TrendingUp size={14} className="mr-2" /> Get Regional Trends</>}
      </Button>

      {result && result.trending_topics.length > 0 && (
        <div className="flex flex-col gap-3">
          {result.trending_topics.map((topic, i) => (
            <div key={i} className="rounded-xl border border-white/[0.06] bg-surface-2 p-4">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-apple-blue/15 text-[10px] font-bold text-apple-blue">
                  {i + 1}
                </span>
                <p className="font-semibold text-ink">{topic.topic}</p>
                <span className={cn('rounded-full border px-2 py-0.5 text-[10px] font-semibold capitalize', URGENCY_COLORS[topic.urgency] ?? URGENCY_COLORS.medium)}>
                  {topic.urgency} urgency
                </span>
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wide text-ink-faint">Why it's relevant</p>
                  <p className="mt-0.5 text-sm text-ink-soft">{topic.relevance_reason}</p>
                </div>
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wide text-ink-faint">Content angle</p>
                  <p className="mt-0.5 text-sm text-ink-soft">{topic.content_angle}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab: Regional Hashtags
// ---------------------------------------------------------------------------

function HashtagsTab() {
  const [region, setRegion] = useState('india');
  const [topic, setTopic] = useState('');
  const [platform, setPlatform] = useState('linkedin');
  const [result, setResult] = useState<RegionalHashtagResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFetch() {
    if (!topic.trim()) { setError('Please enter a topic.'); return; }
    setLoading(true);
    setError(null);
    try {
      const res = await fetchRegionalHashtags({ region, topic: topic.trim(), platform });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate hashtags');
    } finally {
      setLoading(false);
    }
  }

  function HashtagGroup({ label, tags, color }: { label: string; tags: string[]; color: string }) {
    const text = tags.map((t) => (t.startsWith('#') ? t : `#${t}`)).join(' ');
    return (
      <SectionCard title={label} action={<CopyButton text={text} />}>
        <div className="flex flex-wrap gap-2">
          {tags.map((tag, i) => (
            <span
              key={i}
              className={cn('rounded-full border px-2.5 py-1 text-[12px] font-medium', color)}
            >
              {tag.startsWith('#') ? tag : `#${tag}`}
            </span>
          ))}
        </div>
      </SectionCard>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="grid gap-3 sm:grid-cols-3">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-ink">Topic *</label>
          <Input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="e.g. AI for entrepreneurs" disabled={loading} />
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-ink">Region</label>
          <AppSelect value={region} onValueChange={setRegion} options={REGIONS} disabled={loading} />
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-ink">Platform</label>
          <AppSelect value={platform} onValueChange={setPlatform} options={SOCIAL_PLATFORMS} disabled={loading} />
        </div>
      </div>

      {error && <p className="rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-400">{error}</p>}

      <Button onClick={() => void handleFetch()} disabled={loading} className="w-full sm:w-fit">
        {loading
          ? <><Loader2 size={14} className="mr-2 animate-spin" /> Generating…</>
          : <><Hash size={14} className="mr-2" /> Generate Hashtags</>}
      </Button>

      {result && (
        <div className="grid gap-4 sm:grid-cols-3">
          <HashtagGroup label="Primary — High Reach" tags={result.hashtags.primary} color="border-apple-blue/20 bg-apple-blue/10 text-apple-blue" />
          <HashtagGroup label="Secondary — Niche" tags={result.hashtags.secondary} color="border-sky-500/20 bg-sky-500/10 text-sky-400" />
          <HashtagGroup label="Trending Now" tags={result.hashtags.trending} color="border-emerald-500/20 bg-emerald-500/10 text-emerald-400" />
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// History panel
// ---------------------------------------------------------------------------

function HistoryPanel({ items }: { items: RegionalHistoryItem[] }) {
  const [expanded, setExpanded] = useState<number | null>(null);

  if (items.length === 0) return null;

  const typeIcons: Record<string, React.ReactNode> = {
    localise: <Globe size={12} />,
    trending_topics: <TrendingUp size={12} />,
    hashtags: <Hash size={12} />,
  };

  return (
    <section>
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-[0.15em] text-ink-faint">Recent History</h2>
      <div className="flex flex-col gap-2">
        {items.slice(0, 10).map((item) => (
          <div key={item.id} className="rounded-xl border border-white/[0.06] bg-surface-2 overflow-hidden">
            <button
              type="button"
              onClick={() => setExpanded((prev) => (prev === item.id ? null : item.id))}
              className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left transition hover:bg-white/[0.02]"
            >
              <div className="flex items-center gap-3 min-w-0">
                <span className="flex items-center gap-1 rounded-full border border-white/[0.08] bg-white/[0.04] px-2 py-0.5 text-[10px] text-ink-faint capitalize">
                  {typeIcons[item.request_type]} {item.request_type.replace('_', ' ')}
                </span>
                <span className="text-[11px] font-semibold text-ink capitalize">{item.region}</span>
                {item.industry && item.industry !== 'general' && (
                  <span className="text-[11px] text-ink-faint capitalize">{item.industry.replace('_', ' ')}</span>
                )}
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <span className="text-[11px] text-ink-faint">
                  {new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(new Date(item.created_at))}
                </span>
                {expanded === item.id ? <ChevronUp size={13} className="text-ink-faint" /> : <ChevronDown size={13} className="text-ink-faint" />}
              </div>
            </button>
            {expanded === item.id && item.localised_content && (
              <div className="border-t border-white/[0.04] px-4 pb-4 pt-3">
                <p className="text-[10px] font-semibold uppercase tracking-wide text-ink-faint mb-2">Localised Output</p>
                <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink-soft line-clamp-6">{item.localised_content}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function RegionalPage() {
  const [history, setHistory] = useState<RegionalHistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setHistoryLoading(true);
      try {
        const data = await fetchRegionalHistory();
        setHistory(data);
      } catch {
        // non-critical
      } finally {
        setHistoryLoading(false);
      }
    }
    void load();
  }, []);

  return (
    <div className="flex flex-col gap-6 p-4 sm:p-6">
      <PageHeader
        eyebrow="Tools"
        title="Regional Content"
        description="Localise content, discover regional trends, and generate geo-specific hashtag strategies"
      >
        <div className="flex flex-wrap gap-2 text-xs">
          {['🇮🇳 India', '🇺🇸 USA', '🇬🇧 UK', '🇦🇪 UAE', '🇨🇦 Canada', '🌍 Global'].map((r) => (
            <span key={r} className="rounded-full border border-white/[0.06] bg-white/[0.03] px-2.5 py-1 text-ink-faint">{r}</span>
          ))}
        </div>
      </PageHeader>

      <Card className="p-0 overflow-hidden">
        <Tabs defaultValue="localise">
          <div className="border-b border-white/[0.06] px-5 pt-4">
            <TabsList className="h-9 gap-1 rounded-none bg-transparent p-0 border-none">
              {[
                { value: 'localise', label: 'Localise Content', icon: <Globe size={13} /> },
                { value: 'trending', label: 'Regional Trends', icon: <TrendingUp size={13} /> },
                { value: 'hashtags', label: 'Hashtags', icon: <Hash size={13} /> },
              ].map((tab) => (
                <TabsTrigger
                  key={tab.value}
                  value={tab.value}
                  className="flex items-center gap-1.5 rounded-t-md border-b-2 border-transparent px-4 py-2 text-[13px] text-ink-faint data-[state=active]:border-apple-blue data-[state=active]:text-apple-blue data-[state=active]:bg-transparent"
                >
                  {tab.icon}
                  <span>{tab.label}</span>
                </TabsTrigger>
              ))}
            </TabsList>
          </div>

          <div className="p-5">
            <TabsContent value="localise" className="mt-0">
              <LocaliseTab />
            </TabsContent>
            <TabsContent value="trending" className="mt-0">
              <TrendingTopicsTab />
            </TabsContent>
            <TabsContent value="hashtags" className="mt-0">
              <HashtagsTab />
            </TabsContent>
          </div>
        </Tabs>
      </Card>

      {!historyLoading && <HistoryPanel items={history} />}
    </div>
  );
}
