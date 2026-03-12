'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ArrowLeft, Copy, ImageIcon, Loader2 } from 'lucide-react';

import { ImageGeneratorModal } from '@/components/image-generator/ImageGeneratorModal';
import { PageHeader } from '@/components/page-header';
import { PageShell } from '@/components/page-shell';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { fetchPlatformContentHistory } from '@/lib/api';
import type { PlatformContentResponse } from '@/lib/types';
import { cn } from '@/lib/utils';

const PLATFORM_MAP: Record<string, string> = {
  linkedin: 'linkedin', twitter: 'twitter', x: 'twitter',
  instagram: 'instagram', threads: 'threads', youtube: 'youtube',
};

const PLATFORM_BADGES: Record<string, string> = {
  linkedin: 'border-blue-500/20 bg-blue-500/10 text-blue-400',
  twitter: 'border-sky-500/20 bg-sky-500/10 text-sky-400',
  instagram: 'border-pink-500/20 bg-pink-500/10 text-pink-400',
  youtube: 'border-red-500/20 bg-red-500/10 text-red-400',
};

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
      className="flex h-8 w-8 items-center justify-center rounded-md border border-white/[0.06] bg-white/[0.03] text-ink-faint transition hover:border-apple-blue/30 hover:bg-apple-blue/10 hover:text-apple-blue"
    >
      {copied ? (
        <span className="text-xs text-moss">✓</span>
      ) : (
        <Copy size={14} />
      )}
    </button>
  );
}

export default function PlatformContentHistoryDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const itemId = Number(params.id);

  const [loading, setLoading] = useState(true);
  const [item, setItem] = useState<PlatformContentResponse | null>(null);
  const [imageOpen, setImageOpen] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const history = await fetchPlatformContentHistory();
        const found = history.find((h) => h.id === itemId) ?? null;
        setItem(found);
      } catch {
        setItem(null);
      } finally {
        setLoading(false);
      }
    }

    if (Number.isNaN(itemId)) {
      setLoading(false);
      setItem(null);
      return;
    }

    void load();
  }, [itemId]);

  const platformBadge = item
    ? PLATFORM_BADGES[item.platform.toLowerCase()] ??
      'border-white/[0.08] bg-white/[0.04] text-ink-soft'
    : '';

  return (
    <PageShell>
      <PageHeader
        title={item?.topic ?? 'Post'}
        description="Generated platform content"
      >
        <Button asChild variant="outline" size="sm">
          <Link href="/dashboard/flows/trending-post">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Trending
          </Link>
        </Button>
      </PageHeader>

      <div className="flex flex-col gap-6 px-4 sm:px-6 lg:px-8">
        {loading ? (
          <div className="flex items-center gap-2 py-12 text-sm text-ink-soft">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading...
          </div>
        ) : item ? (
          <Card className="border-white/[0.06] bg-card">
            <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3 border-b border-white/[0.06]">
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={cn(
                    'rounded-full border px-2.5 py-0.5 text-xs font-semibold',
                    platformBadge
                  )}
                >
                  {item.platform}
                </span>
                <span className="rounded-full border border-white/[0.06] bg-white/[0.04] px-2.5 py-0.5 text-xs text-ink-soft">
                  {prettyContentType(item.content_type)}
                </span>
                <span className="text-xs text-ink-faint">
                  {new Date(item.created_at).toLocaleString(undefined, {
                    dateStyle: 'medium',
                    timeStyle: 'short',
                  })}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Button size="sm" variant="outline" className="h-8 gap-1.5 text-xs" onClick={() => setImageOpen(true)}>
                  <ImageIcon size={13} /> Generate Image
                </Button>
                <CopyButton text={item.content} />
              </div>
            </CardHeader>
            <CardContent className="pt-4">
              <pre className="whitespace-pre-wrap rounded-lg border border-white/[0.06] bg-white/[0.02] p-4 text-sm leading-relaxed text-ink">
                {item.content}
              </pre>
            </CardContent>
          </Card>
        ) : (
          <div className="flex flex-col items-center gap-4 py-12">
            <p className="text-sm text-ink-soft">Post not found.</p>
            <Button variant="outline" size="sm" onClick={() => router.back()}>
              Go back
            </Button>
          </div>
        )}
      </div>

      {item && (
        <ImageGeneratorModal
          open={imageOpen}
          onOpenChange={setImageOpen}
          content={item.content}
          platform={(PLATFORM_MAP[item.platform.toLowerCase()] ?? 'linkedin') as Parameters<typeof ImageGeneratorModal>[0]['platform']}
          contentType={item.content_type}
        />
      )}
    </PageShell>
  );
}
