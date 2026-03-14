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
import { fetchThoughtLeadershipHistory, publishToSocial } from '@/lib/api';
import type { ThoughtLeadershipContentType, ThoughtLeadershipResponse } from '@/lib/types';

const LEADERSHIP_LABELS_MAP: Record<ThoughtLeadershipContentType, string> = {
  deep_insight: 'Deep Insight',
  predictions: 'Industry Predictions',
  contrarian: 'Contrarian View',
  framework: 'Framework Post',
  case_study: 'Case Study Breakdown',
  authority_thread: 'Authority Thread',
  hard_truths: 'Hard Truths',
  founder_journey: 'Founder Journey',
  myth_busting: 'Myth Busting',
};

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
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'twitter', label: 'X / Twitter' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'facebook', label: 'Facebook' },
];

export default function ThoughtLeadershipHistoryDetailPage() {
  const params = useParams<{ id: string }>();
  const itemId = Number(params.id);
  const [loading, setLoading] = useState(true);
  const [item, setItem] = useState<ThoughtLeadershipResponse | null>(null);
  const [imageOpen, setImageOpen] = useState(false);
  const [publishOpen, setPublishOpen] = useState(false);
  const [publishPlatform, setPublishPlatform] = useState('linkedin');
  const [publishImageUrl, setPublishImageUrl] = useState('');
  const [publishing, setPublishing] = useState(false);
  const [publishOutcome, setPublishOutcome] = useState<'posted' | 'failed' | null>(null);
  const [publishError, setPublishError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const history = await fetchThoughtLeadershipHistory();
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

  const typeLabel = item
    ? (LEADERSHIP_LABELS_MAP[item.content_type as ThoughtLeadershipContentType] ?? item.content_type)
    : '';

  return (
    <PageShell>
      <PageHeader
        title={item?.topic ?? 'Thought Leadership'}
        description={item ? `${item.industry} · ${typeLabel}` : undefined}
      >
        <Button asChild variant="outline" size="sm">
          <Link href="/dashboard/thought-leadership">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Thought Leadership
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
            <CardHeader className="flex flex-row items-center justify-between gap-3 border-b border-white/[0.06]">
              <span className="inline-flex rounded-full border border-moss/20 bg-moss/15 px-2.5 py-0.5 text-xs font-semibold text-moss">
                {typeLabel}
              </span>
              <div className="flex items-center gap-2 flex-wrap justify-end">
                {publishOutcome === 'posted' ? (
                  <span className="flex items-center gap-1 text-xs font-semibold text-emerald-400"><Check size={13} /> Posted!</span>
                ) : publishOpen ? (
                  <>
                    <select
                      value={publishPlatform}
                      onChange={(e) => setPublishPlatform(e.target.value)}
                      className="h-8 rounded-md border border-white/[0.08] bg-surface-2 px-2 text-xs text-ink focus:border-apple-blue/30 focus:outline-none"
                    >
                      {PLATFORM_OPTIONS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
                    </select>
                    <input
                      type="url"
                      value={publishImageUrl}
                      onChange={(e) => setPublishImageUrl(e.target.value)}
                      placeholder="Image URL (optional)"
                      className="h-8 w-44 rounded-md border border-white/[0.08] bg-surface-2 px-2 text-xs text-ink placeholder-ink-faint focus:border-apple-blue/30 focus:outline-none"
                    />
                    <Button
                      size="sm"
                      className="h-8 gap-1.5 text-xs"
                      disabled={publishing}
                      onClick={async () => {
                        setPublishing(true);
                        setPublishError(null);
                        try {
                          await publishToSocial(item.content, publishPlatform, publishImageUrl || undefined);
                          setPublishOutcome('posted');
                          setPublishOpen(false);
                        } catch (err) {
                          setPublishOutcome('failed');
                          setPublishError(err instanceof Error ? err.message : 'Failed');
                        } finally {
                          setPublishing(false);
                        }
                      }}
                    >
                      {publishing ? <Loader2 size={13} className="animate-spin" /> : <Check size={13} />}
                      Post Now
                    </Button>
                    <button type="button" onClick={() => setPublishOpen(false)} className="text-ink-faint hover:text-ink"><X size={14} /></button>
                  </>
                ) : (
                  <Button size="sm" variant="outline" className="h-8 gap-1.5 text-xs" onClick={() => setPublishOpen(true)}>
                    <Send size={13} /> Approve & Publish
                  </Button>
                )}
                <Button size="sm" variant="outline" className="h-8 gap-1.5 text-xs" onClick={() => setImageOpen(true)}>
                  <ImageIcon size={13} /> Generate Image
                </Button>
                <CopyButton text={item.content} />
              </div>
            </CardHeader>
            <CardContent className="pt-4">
              {publishOutcome === 'failed' && (
                <div className="mb-3 rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-xs text-red-400">
                  {publishError ?? 'Publish failed. Check your API credentials in .env.'}
                </div>
              )}
              <pre className="whitespace-pre-wrap rounded-lg border border-white/[0.06] bg-white/[0.02] p-4 text-sm leading-relaxed text-ink">
                {item.content}
              </pre>
            </CardContent>
          </Card>
        ) : (
          <div className="flex flex-col items-center gap-4 py-12">
            <p className="text-sm text-ink-soft">Item not found.</p>
            <Button asChild variant="outline" size="sm">
              <Link href="/dashboard/thought-leadership">Back to Thought Leadership</Link>
            </Button>
          </div>
        )}
      </div>

      {item && (
        <ImageGeneratorModal
          open={imageOpen}
          onOpenChange={setImageOpen}
          content={item.content}
          platform="linkedin"
          contentType={item.content_type}
        />
      )}
    </PageShell>
  );
}
