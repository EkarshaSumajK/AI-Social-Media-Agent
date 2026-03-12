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
import { fetchThoughtLeadershipHistory, generateThoughtLeadership } from '@/lib/api';
import type { ThoughtLeadershipContentType, ThoughtLeadershipResponse } from '@/lib/types';
import { LEADERSHIP_TYPES } from '@/lib/types';
import { cn } from '@/lib/utils';

const LEADERSHIP_LABELS: Record<ThoughtLeadershipContentType, string> = {
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

function formatDate(iso: string) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  }).format(new Date(iso));
}

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
      className="flex h-7 w-7 items-center justify-center rounded-md border border-white/[0.06] bg-white/[0.03] text-ink-faint transition hover:border-apple-blue/30 hover:bg-apple-blue/10 hover:text-apple-blue"
    >
      {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
    </button>
  );
}

export default function ThoughtLeadershipPage() {
  const [topic, setTopic] = useState('AI positioning for B2B founders');
  const [industry, setIndustry] = useState('SaaS');
  const [contentType, setContentType] = useState<ThoughtLeadershipContentType>('deep_insight');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [history, setHistory] = useState<ThoughtLeadershipResponse[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setHistoryLoading(true);
      try {
        const data = await fetchThoughtLeadershipHistory();
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
    const trimmedIndustry = industry.trim();

    if (!trimmedTopic) { setError('Please enter a topic.'); return; }
    if (!trimmedIndustry) { setError('Please enter an industry.'); return; }

    setLoading(true);
    setError(null);

    try {
      const res = await generateThoughtLeadership({
        topic: trimmedTopic,
        content_type: contentType,
        industry: trimmedIndustry,
      });
      setHistory((prev) => [res, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate thought leadership content');
    } finally {
      setLoading(false);
    }
  }

  const selectedLabel = LEADERSHIP_LABELS[contentType];

  return (
    <PageShell>
      <PageHeader
        title="Thought Leadership"
        description="Generate structured thought-leadership assets with backend content-type contracts"
      />

      <section className="rounded-lg border bg-card p-5 text-card-foreground shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-ink">Configuration</h2>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="md:col-span-2">
            <label className="mb-1.5 block text-sm font-medium text-ink">Topic</label>
            <Input
              value={topic}
              onChange={(event) => setTopic(event.target.value)}
              placeholder="e.g. Building trust with AI-generated content"
              disabled={loading}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-ink">Industry</label>
            <Input
              value={industry}
              onChange={(event) => setIndustry(event.target.value)}
              placeholder="e.g. SaaS, education, healthcare"
              disabled={loading}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-ink">Content type</label>
            <AppSelect
              value={contentType}
              onValueChange={(value) => setContentType(value as ThoughtLeadershipContentType)}
              disabled={loading}
              options={LEADERSHIP_TYPES}
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
            `Generate ${selectedLabel}`
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
                const typeLabel = LEADERSHIP_LABELS[item.content_type as ThoughtLeadershipContentType] || item.content_type;
                return (
                  <ListCard
                    key={item.id}
                    title={item.topic}
                    metadata={
                      <>
                        <span>{item.industry}</span>
                        <span>•</span>
                        <span>{formatDate(item.created_at)}</span>
                      </>
                    }
                    tags={
                      <span className="rounded-md border border-moss/20 bg-moss/15 px-2 py-0.5 text-xs font-medium text-moss">
                        {typeLabel}
                      </span>
                    }
                    actions={[{ label: 'View details', href: `/dashboard/thought-leadership/history/${item.id}` }]}
                    href={`/dashboard/thought-leadership/history/${item.id}`}
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
