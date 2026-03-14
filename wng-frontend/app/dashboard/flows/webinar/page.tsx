'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { CalendarDays, Loader2, Megaphone } from 'lucide-react';

import { ListCard } from '@/components/list-card';
import { PageHeader } from '@/components/page-header';
import { PageShell } from '@/components/page-shell';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { createCampaign, fetchCampaigns, generateCampaignContent } from '@/lib/api';
import type { Campaign } from '@/lib/types';
import { cn } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PLATFORM_OPTIONS = [
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'twitter', label: 'X / Twitter' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'youtube', label: 'YouTube' },
  { value: 'facebook', label: 'Facebook' },
];

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function WebinarFlowPage() {
  const router = useRouter();
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<Campaign[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);

  const [title, setTitle] = useState('');
  const [eventDate, setEventDate] = useState('');
  const [goal, setGoal] = useState('');
  const [audience, setAudience] = useState('');
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(['linkedin', 'twitter']);

  useEffect(() => {
    void fetchCampaigns()
      .then((data) => { setHistory(data); setHistoryLoading(false); })
      .catch(() => setHistoryLoading(false));
  }, []);

  function togglePlatform(value: string) {
    setSelectedPlatforms((prev) =>
      prev.includes(value) ? prev.filter((p) => p !== value) : [...prev, value],
    );
  }

  async function handleCreate() {
    if (!title.trim()) { setError('Event title is required.'); return; }
    setError(null);
    setGenerating(true);

    try {
      const created = await createCampaign({
        title: title.trim(),
        event_date: eventDate ? new Date(eventDate).toISOString() : undefined,
        goal: goal.trim() || undefined,
        audience: audience.trim() || undefined,
        platforms: selectedPlatforms,
        platform_entity: 'horizon',
      });

      await generateCampaignContent(created.id);
      void fetchCampaigns().then(setHistory).catch(() => null);
      router.push(`/dashboard/campaigns/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create campaign');
    } finally {
      setGenerating(false);
    }
  }

  return (
    <PageShell>
      <PageHeader
        title="Webinar / Event Campaign"
        description="Generate a full pre, during, and post-event content plan in one click"
        eyebrow="Flow"
      />

      <div className="flex flex-col gap-6">
        {error && (
          <div className="rounded-lg border border-ember/30 bg-ember/5 px-4 py-3 text-sm text-ember">
            {error}
          </div>
        )}

        <section className="rounded-xl border border-white/[0.06] bg-card p-6 text-card-foreground shadow-sm">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="md:col-span-2">
                <label className="mb-1.5 block text-sm font-medium text-ink">
                  Event / Webinar Title <span className="text-ember">*</span>
                </label>
                <Input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. How to Scale Your SaaS with AI"
                  onKeyDown={(e) => { if (e.key === 'Enter') void handleCreate(); }}
                  disabled={generating}
                  className="border-white/[0.08] bg-white/[0.03]"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium text-ink">Event Date</label>
                <Input
                  type="datetime-local"
                  value={eventDate}
                  onChange={(e) => setEventDate(e.target.value)}
                  disabled={generating}
                  className="border-white/[0.08] bg-white/[0.03]"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium text-ink">Goal</label>
                <Input
                  value={goal}
                  onChange={(e) => setGoal(e.target.value)}
                  placeholder="e.g. Lead generation, brand awareness"
                  disabled={generating}
                  className="border-white/[0.08] bg-white/[0.03]"
                />
              </div>

              <div className="md:col-span-2">
                <label className="mb-1.5 block text-sm font-medium text-ink">Target Audience</label>
                <Input
                  value={audience}
                  onChange={(e) => setAudience(e.target.value)}
                  placeholder="e.g. SaaS founders and product managers"
                  disabled={generating}
                  className="border-white/[0.08] bg-white/[0.03]"
                />
              </div>

              <div className="md:col-span-2">
                <label className="mb-2 block text-sm font-medium text-ink">Platforms</label>
                <div className="flex flex-wrap gap-2">
                  {PLATFORM_OPTIONS.map((p) => (
                    <button
                      key={p.value}
                      type="button"
                      onClick={() => togglePlatform(p.value)}
                      disabled={generating}
                      className={cn(
                        'rounded-full border px-3 py-1 text-xs font-medium transition',
                        selectedPlatforms.includes(p.value)
                          ? 'border-apple-blue/40 bg-apple-blue/10 text-apple-blue'
                          : 'border-white/[0.06] bg-white/[0.02] text-ink-soft hover:border-apple-blue/30 hover:text-ink',
                      )}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-6 flex items-center gap-3 border-t border-white/[0.06] pt-5">
              <Button onClick={handleCreate} className="min-w-[200px]" disabled={generating}>
                {generating ? (
                  <>
                    <Loader2 size={14} className="mr-2 animate-spin" />
                    Creating & generating...
                  </>
                ) : (
                  <>
                    <Megaphone size={14} className="mr-2" />
                    Create & Generate Campaign
                  </>
                )}
              </Button>
              <p className="text-xs text-ink-faint">AI generates 3–4 pieces per phase. You’ll be taken to the campaign detail page.</p>
            </div>
        </section>

        {/* Past campaigns */}
        <section className="rounded-lg border border-white/[0.06] bg-card text-card-foreground shadow-sm">
          <div className="flex items-center justify-between gap-3 border-b border-white/[0.06] px-5 py-4">
            <div>
              <h2 className="text-base font-semibold text-ink">Past Campaigns</h2>
              <p className="text-xs text-ink-soft">Your webinar and event campaigns — click to view content</p>
            </div>
            {!historyLoading && history.length > 0 && (
              <span className="rounded-full bg-white/[0.06] px-3 py-1 text-xs font-semibold text-ink-soft">
                {history.length} {history.length === 1 ? 'campaign' : 'campaigns'}
              </span>
            )}
          </div>

          <div className="p-5">
            {historyLoading ? (
              <div className="flex items-center gap-2 py-12 text-sm text-ink-soft">
                <Loader2 size={14} className="animate-spin" />
                Loading campaigns...
              </div>
            ) : history.length === 0 ? (
              <div className="flex flex-col items-center gap-4 rounded-lg border border-dashed border-white/[0.08] bg-white/[0.02] py-16">
                <CalendarDays size={40} className="text-ink-faint" />
                <p className="text-sm text-ink-soft">No campaigns yet.</p>
                <p className="text-xs text-ink-faint">Create your first campaign above.</p>
              </div>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {history.map((campaign) => {
                  const pieceCount = campaign.pieces?.length ?? 0;
                  return (
                    <ListCard
                      key={campaign.id}
                      title={campaign.title || 'Untitled campaign'}
                      status={campaign.status}
                      statusClassName={
                        campaign.status === 'active'
                          ? 'border-moss/30 bg-moss/10 text-moss'
                          : campaign.status === 'draft'
                            ? undefined
                            : 'border-apple-blue/20 bg-apple-blue/10 text-apple-blue'
                      }
                      metadata={
                        <>
                          <span>horizon</span>
                          {campaign.goal && (
                            <>
                              <span>•</span>
                              <span>{campaign.goal}</span>
                            </>
                          )}
                          <span>•</span>
                          <span>{formatDate(campaign.created_at)}</span>
                        </>
                      }
                      tags={
                        <>
                          {campaign.platforms?.map((p) => (
                            <span
                              key={p}
                              className="rounded-md border border-apple-blue/20 bg-apple-blue/10 px-2 py-0.5 text-xs font-medium text-apple-blue"
                            >
                              {p}
                            </span>
                          ))}
                          <span className="rounded-md border border-white/[0.06] bg-white/[0.04] px-2 py-0.5 text-xs text-ink-soft">
                            {pieceCount} pieces
                          </span>
                        </>
                      }
                      actions={[
                        { label: 'View details', href: `/dashboard/campaigns/${campaign.id}` },
                      ]}
                      href={`/dashboard/campaigns/${campaign.id}`}
                    />
                  );
                })}
              </div>
            )}
          </div>
        </section>
      </div>
    </PageShell>
  );
}
