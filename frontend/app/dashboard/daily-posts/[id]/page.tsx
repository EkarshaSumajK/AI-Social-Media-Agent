'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ArrowLeft, Check, Copy, ImageIcon, Loader2, Send, X } from 'lucide-react';

import { ImageGeneratorModal } from '@/components/image-generator/ImageGeneratorModal';
import { PageHeader } from '@/components/page-header';
import { PageShell } from '@/components/page-shell';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { fetchDailyPostsHistory, publishToSocial } from '@/lib/api';
import type { DailyPostBatch, DailyPostSuggestion } from '@/lib/types';
import { cn } from '@/lib/utils';

const PLATFORM_MAP: Record<string, string> = {
  twitter: 'twitter', 'x / twitter': 'twitter', x: 'twitter',
  linkedin: 'linkedin', instagram: 'instagram', 'instagram reels': 'instagram',
  threads: 'threads', youtube: 'youtube', facebook: 'facebook',
};

const POST_TYPE_STYLES: Record<string, { label: string; badge: string }> = {
  trending_topic: { label: 'Trending Topic', badge: 'bg-apple-blue/15 text-apple-blue border-apple-blue/20' },
  authority: { label: 'Authority', badge: 'bg-moss/15 text-moss border-moss/20' },
  engagement: { label: 'Engagement', badge: 'bg-ocean/15 text-ocean border-ocean/20' },
  storytelling: { label: 'Storytelling', badge: 'bg-violet-500/15 text-violet-400 border-violet-500/20' },
  short_form_video: { label: 'Short-form Video', badge: 'bg-ember/15 text-ember border-ember/20' },
};

const PLATFORM_STYLES: Record<string, { label: string; badge: string }> = {
  twitter: { label: 'X / Twitter', badge: 'bg-sky-500/10 text-sky-400 border-sky-500/20' },
  linkedin: { label: 'LinkedIn', badge: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
  instagram: { label: 'Instagram', badge: 'bg-pink-500/10 text-pink-400 border-pink-500/20' },
  youtube: { label: 'YouTube', badge: 'bg-red-500/10 text-red-400 border-red-500/20' },
  facebook: { label: 'Facebook', badge: 'bg-blue-600/10 text-blue-300 border-blue-600/20' },
};

function getPostTypeStyle(type: string) {
  return POST_TYPE_STYLES[type.toLowerCase()] ?? {
    label: type.replace(/_/g, ' '),
    badge: 'bg-apple-blue/15 text-apple-blue border-apple-blue/20',
  };
}

function getPlatformStyle(hint: string) {
  return PLATFORM_STYLES[hint?.toLowerCase() ?? ''] ?? { label: hint, badge: 'bg-white/[0.06] text-ink-soft border-white/[0.08]' };
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
      className="flex h-8 w-8 items-center justify-center rounded-md border border-white/[0.06] bg-white/[0.03] text-ink-faint transition hover:border-apple-blue/30 hover:bg-apple-blue/10 hover:text-apple-blue"
    >
      {copied ? <Check size={14} className="text-moss" /> : <Copy size={14} />}
    </button>
  );
}

const PLATFORM_OPTIONS = [
  { value: 'twitter', label: 'X / Twitter' },
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'facebook', label: 'Facebook' },
];

function ApprovePublishButton({ content, defaultPlatform }: { content: string; defaultPlatform?: string }) {
  const [open, setOpen] = useState(false);
  const [platform, setPlatform] = useState(defaultPlatform ?? 'linkedin');
  const [imageUrl, setImageUrl] = useState('');
  const [posting, setPosting] = useState(false);
  const [outcome, setOutcome] = useState<'posted' | 'failed' | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (outcome === 'posted') {
    return <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-400"><Check size={12} /> Posted!</span>;
  }

  if (!open) {
    return (
      <Button size="sm" variant="outline" className="h-7 gap-1 px-2 text-[11px]" onClick={() => setOpen(true)}>
        <Send size={11} /> Approve & Publish
      </Button>
    );
  }

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <select
        value={platform}
        onChange={(e) => setPlatform(e.target.value)}
        className="h-7 rounded-md border border-white/[0.08] bg-surface-2 px-2 text-[11px] text-ink focus:border-apple-blue/30 focus:outline-none"
      >
        {PLATFORM_OPTIONS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
      </select>
      <input
        type="url"
        value={imageUrl}
        onChange={(e) => setImageUrl(e.target.value)}
        placeholder="Image URL (optional)"
        className="h-7 flex-1 min-w-[130px] rounded-md border border-white/[0.08] bg-surface-2 px-2 text-[11px] text-ink placeholder-ink-faint focus:border-apple-blue/30 focus:outline-none"
      />
      <Button
        size="sm"
        className="h-7 gap-1 px-2 text-[11px]"
        disabled={posting}
        onClick={async () => {
          setPosting(true);
          setError(null);
          try {
            await publishToSocial(content, platform, imageUrl || undefined);
            setOutcome('posted');
            setOpen(false);
          } catch (err) {
            setOutcome('failed');
            setError(err instanceof Error ? err.message : 'Failed');
          } finally {
            setPosting(false);
          }
        }}
      >
        {posting ? <Loader2 size={11} className="animate-spin" /> : <Check size={11} />}
        Post Now
      </Button>
      <button type="button" onClick={() => setOpen(false)} className="text-ink-faint hover:text-ink">
        <X size={13} />
      </button>
      {outcome === 'failed' && <span className="w-full text-[10px] text-red-400">{error ?? 'Failed'}</span>}
    </div>
  );
}

function PostCard({ post, index, onGenerateImage }: { post: DailyPostSuggestion; index: number; onGenerateImage: () => void }) {
  const typeStyle = getPostTypeStyle(post.post_type);
  const platformStyle = post.platform_hint ? getPlatformStyle(post.platform_hint) : null;

  return (
    <Card className="border-white/[0.06] bg-card overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between gap-2 border-b border-white/[0.04] py-3">
        <div className="flex items-center gap-2">
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-white/[0.06] text-[10px] font-bold text-ink-faint">
            {index + 1}
          </span>
          <span className={cn('rounded-full border px-2.5 py-0.5 text-xs font-semibold', typeStyle.badge)}>
            {typeStyle.label}
          </span>
          {platformStyle && (
            <span className={cn('rounded-full border px-2 py-0.5 text-[11px]', platformStyle.badge)}>
              {platformStyle.label}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 flex-wrap justify-end">
          <ApprovePublishButton
            content={post.content}
            defaultPlatform={PLATFORM_MAP[post.platform_hint?.toLowerCase() ?? ''] ?? 'linkedin'}
          />
          <Button size="sm" variant="outline" className="h-7 gap-1.5 text-xs px-2" onClick={onGenerateImage}>
            <ImageIcon size={12} />
            Image
          </Button>
          <CopyButton text={post.content} />
        </div>
      </CardHeader>
      <CardContent className="py-4">
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink">{post.content}</p>
      </CardContent>
    </Card>
  );
}

export default function DailyPostBatchDetailPage() {
  const params = useParams<{ id: string }>();
  const batchId = Number(params.id);
  const [loading, setLoading] = useState(true);
  const [batch, setBatch] = useState<DailyPostBatch | null>(null);
  const [imageModal, setImageModal] = useState<{ open: boolean; post: DailyPostSuggestion | null }>({ open: false, post: null });

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const history = await fetchDailyPostsHistory();
        const found = history.find((b) => b.id === batchId) ?? null;
        setBatch(found);
      } catch {
        setBatch(null);
      } finally {
        setLoading(false);
      }
    }

    if (Number.isNaN(batchId)) {
      setLoading(false);
      setBatch(null);
      return;
    }
    void load();
  }, [batchId]);

  const goalLabel = batch
    ? { brand: 'Brand Awareness', leads: 'Lead Generation', sales: 'Sales Conversion' }[batch.business_goal] ?? batch.business_goal
    : '';

  return (
    <PageShell>
      <PageHeader
        title={batch ? `${batch.industry} · ${batch.region}` : 'Batch'}
        description={batch ? `${batch.target_audience} · ${goalLabel}` : undefined}
      >
        <Button asChild variant="outline" size="sm">
          <Link href="/dashboard/daily-posts">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Daily Posts
          </Link>
        </Button>
      </PageHeader>

      <div className="flex flex-col gap-6 px-4 sm:px-6 lg:px-8">
        {loading ? (
          <div className="flex items-center gap-2 py-12 text-sm text-ink-soft">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading...
          </div>
        ) : batch ? (
          <div className="grid gap-4 lg:grid-cols-2">
            {batch.suggestions.map((post, i) => (
              <PostCard
                key={`${batch.id}-${post.post_type}-${i}`}
                post={post}
                index={i}
                onGenerateImage={() => setImageModal({ open: true, post })}
              />
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4 py-12">
            <p className="text-sm text-ink-soft">Batch not found.</p>
            <Button asChild variant="outline" size="sm">
              <Link href="/dashboard/daily-posts">Back to Daily Posts</Link>
            </Button>
          </div>
        )}
      </div>

      {imageModal.post && (
        <ImageGeneratorModal
          open={imageModal.open}
          onOpenChange={(open) => setImageModal((s) => ({ ...s, open }))}
          content={imageModal.post.content}
          platform={(PLATFORM_MAP[imageModal.post.platform_hint?.toLowerCase() ?? ''] ?? 'linkedin') as Parameters<typeof ImageGeneratorModal>[0]['platform']}
          contentType={imageModal.post.post_type}
        />
      )}
    </PageShell>
  );
}
