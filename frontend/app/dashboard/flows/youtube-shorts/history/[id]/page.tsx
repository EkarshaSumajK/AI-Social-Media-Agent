'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ArrowLeft, Check, Copy, Loader2 } from 'lucide-react';

import { PageHeader } from '@/components/page-header';
import { PageShell } from '@/components/page-shell';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { fetchYoutubeShortsHistory } from '@/lib/api';
import type { YoutubeShortResponse } from '@/lib/types';

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

function OutputSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-4">
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-ink-faint">{title}</h3>
      {children}
    </div>
  );
}

export default function YoutubeShortHistoryDetailPage() {
  const params = useParams<{ id: string }>();
  const itemId = Number(params.id);
  const [loading, setLoading] = useState(true);
  const [item, setItem] = useState<YoutubeShortResponse | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const history = await fetchYoutubeShortsHistory();
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

  return (
    <PageShell>
      <PageHeader
        title={item?.topic ?? 'YouTube Short'}
        description={item ? `${item.duration}s · ${item.target_audience ?? 'General'}` : undefined}
      >
        <Button asChild variant="outline" size="sm">
          <Link href="/dashboard/flows/youtube-shorts">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to YouTube Shorts
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
          <div className="space-y-6">
            <OutputSection title="Hook">
              <p className="text-sm leading-relaxed text-ink">{item.hook}</p>
              <CopyButton text={item.hook} />
            </OutputSection>

            <OutputSection title="Script">
              <div className="space-y-4">
                <p className="text-sm text-ink">{(item.script as any).intro}</p>
                {((item.script as any).main_points || []).map((pt: any, i: number) => (
                  <div key={i} className="rounded border border-white/[0.06] p-3">
                    <p className="mb-1 text-xs font-semibold text-apple-blue">{pt.title}</p>
                    <p className="text-sm text-ink">{pt.content}</p>
                  </div>
                ))}
                <p className="text-sm text-ink">{(item.script as any).cta}</p>
              </div>
            </OutputSection>

            <OutputSection title="Titles">
              <ul className="space-y-1">
                {item.titles.map((t, i) => (
                  <li key={i} className="text-sm text-ink">{t}</li>
                ))}
              </ul>
            </OutputSection>

            <OutputSection title="Description">
              <p className="whitespace-pre-wrap text-sm text-ink">{item.description}</p>
            </OutputSection>

            <OutputSection title="Tags">
              <div className="flex flex-wrap gap-2">
                {item.tags.map((tag, i) => (
                  <span
                    key={i}
                    className="rounded-md border border-white/[0.06] bg-white/[0.04] px-2 py-0.5 text-xs text-ink-soft"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </OutputSection>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4 py-12">
            <p className="text-sm text-ink-soft">Short not found.</p>
            <Button asChild variant="outline" size="sm">
              <Link href="/dashboard/flows/youtube-shorts">Back to YouTube Shorts</Link>
            </Button>
          </div>
        )}
      </div>
    </PageShell>
  );
}
