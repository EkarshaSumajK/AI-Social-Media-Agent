'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, CalendarDays, Layers3, Loader2, Megaphone, Sparkles } from 'lucide-react';

import { AIImageButton } from '@/components/ai-image-button';
import { PageHeader } from '@/components/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { fetchCampaign, generateCampaignContent } from '@/lib/api';
import type { Campaign, CampaignPiece } from '@/lib/types';

const PHASE_ORDER = ['pre', 'during', 'post'] as const;

const PHASE_LABELS: Record<string, string> = {
  pre: 'Pre Event',
  during: 'During Event',
  post: 'Post Event',
};

const SOCIAL_PLATFORM_LABELS: Record<string, string> = {
  linkedin: 'LinkedIn',
  instagram: 'Instagram',
  twitter: 'X (Twitter)',
  facebook: 'Facebook',
  youtube: 'YouTube',
};

function formatPhase(phase: string) {
  return PHASE_LABELS[phase] || phase.replace(/_/g, ' ');
}

function formatPlatform(value: string | null | undefined) {
  if (!value) return 'Any';
  return SOCIAL_PLATFORM_LABELS[value] || value;
}

export default function CampaignDetailPage() {
  const params = useParams<{ id: string }>();
  const campaignId = Number(params.id);

  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [campaign, setCampaign] = useState<Campaign | null>(null);

  async function loadCampaign() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCampaign(campaignId);
      setCampaign(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load campaign');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (Number.isNaN(campaignId)) {
      setLoading(false);
      setError('Invalid campaign id');
      return;
    }
    void loadCampaign();
  }, [campaignId]);

  const piecesByPhase = useMemo(() => {
    const grouped: Record<string, CampaignPiece[]> = {};
    for (const piece of campaign?.pieces ?? []) {
      const phase = piece.phase || 'other';
      if (!grouped[phase]) {
        grouped[phase] = [];
      }
      grouped[phase].push(piece);
    }
    return grouped;
  }, [campaign?.pieces]);

  const sortedPhases = useMemo(() => {
    const phaseKeys = Object.keys(piecesByPhase);
    return phaseKeys.sort((a, b) => {
      const indexA = PHASE_ORDER.indexOf(a as (typeof PHASE_ORDER)[number]);
      const indexB = PHASE_ORDER.indexOf(b as (typeof PHASE_ORDER)[number]);
      const normalizedA = indexA === -1 ? Number.MAX_SAFE_INTEGER : indexA;
      const normalizedB = indexB === -1 ? Number.MAX_SAFE_INTEGER : indexB;
      if (normalizedA === normalizedB) return a.localeCompare(b);
      return normalizedA - normalizedB;
    });
  }, [piecesByPhase]);

  async function handleGenerate() {
    if (!campaign) return;
    setGenerating(true);
    setError(null);
    setMessage(null);

    try {
      const result = await generateCampaignContent(campaign.id) as { pieces_created: number };
      setMessage(`Generated ${result.pieces_created} pieces.`);
      await loadCampaign();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate campaign content');
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="flex flex-col">
      <PageHeader title={campaign?.title || 'Campaign Detail'} description="Detailed campaign plan and generated content pieces">
        <Button asChild variant="outline" size="sm">
          <Link href="/dashboard/campaigns">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to campaigns
          </Link>
        </Button>
      </PageHeader>

      <div className="flex flex-col gap-6 p-4 sm:p-6">
        {error && <div className="rounded-xl border border-ember/30 bg-ember/5 px-4 py-3 text-sm text-ember">{error}</div>}
        {message && <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-400">{message}</div>}

        {loading ? (
          <div className="flex items-center gap-2 text-sm text-ink-soft">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading campaign...
          </div>
        ) : campaign ? (
          <>
            <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <MetricCard icon={Megaphone} label="Status" value={campaign.status} />
              <MetricCard icon={Sparkles} label="Entity" value={campaign.platform_entity} />
              <MetricCard
                icon={CalendarDays}
                label="Event Date"
                value={campaign.event_date ? new Date(campaign.event_date).toLocaleDateString() : 'Not set'}
              />
              <MetricCard icon={Layers3} label="Pieces" value={String((campaign.pieces || []).length)} />
            </section>

            <section className="rounded-lg border bg-card p-5 text-card-foreground shadow-sm">
              <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                <h2 className="text-lg font-semibold text-ink">Campaign overview</h2>
                <Button type="button" variant="secondary" onClick={handleGenerate} disabled={generating}>
                  {generating ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    'Generate content'
                  )}
                </Button>
              </div>

              <dl className="grid gap-4 md:grid-cols-2">
                <InfoBlock label="Goal" value={campaign.goal || 'Not set'} />
                <InfoBlock label="Audience" value={campaign.audience_description || 'Not set'} />
                <InfoBlock label="Created" value={new Date(campaign.created_at).toLocaleString()} />
                <div>
                  <dt className="mb-1 text-xs font-semibold uppercase tracking-[0.18em] text-ink-faint">Platforms</dt>
                  <dd className="flex flex-wrap gap-2">
                    {(campaign.platforms || []).length > 0 ? (
                      (campaign.platforms || []).map((platform) => (
                        <Badge key={platform} variant="outline" className="text-xs">
                          {formatPlatform(platform)}
                        </Badge>
                      ))
                    ) : (
                      <span className="text-sm text-ink-soft">All platforms</span>
                    )}
                  </dd>
                </div>
              </dl>
            </section>

            <section className="rounded-lg border bg-card p-5 text-card-foreground shadow-sm">
              <h2 className="mb-4 text-lg font-semibold text-ink">Generated pieces</h2>
              {sortedPhases.length === 0 ? (
                <p className="text-sm text-ink-soft">No pieces generated yet. Run generation to populate this view.</p>
              ) : (
                <div className="grid gap-4">
                  {sortedPhases.map((phase) => (
                    <article key={phase} className="rounded-lg border border-white/[0.06] bg-surface-2 p-4">
                      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                        <h3 className="font-semibold text-ink">{formatPhase(phase)}</h3>
                        <span className="text-xs text-ink-soft">{piecesByPhase[phase].length} pieces</span>
                      </div>
                      <div className="grid gap-3 md:grid-cols-2">
                        {piecesByPhase[phase].map((piece) => (
                          <div key={piece.id} className="rounded-md border border-white/[0.06] bg-surface-3 p-3">
                            <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
                              <Badge variant="outline" className="text-[11px]">
                                {piece.content_type}
                              </Badge>
                              <span className="text-ink-faint">{formatPlatform(piece.platform)}</span>
                              <AIImageButton
                                caption={piece.content}
                                platform={piece.platform || 'instagram'}
                                title={`${formatPhase(phase)} - ${piece.content_type}`}
                              />
                            </div>
                            <p className="whitespace-pre-wrap break-words text-sm text-ink">{piece.content}</p>
                          </div>
                        ))}
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </section>
          </>
        ) : (
          <p className="text-sm text-ink-soft">Campaign not found.</p>
        )}
      </div>
    </div>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border bg-card p-4 text-card-foreground shadow-sm">
      <div className="mb-2 flex items-center gap-2 text-ink-soft">
        <Icon className="h-4 w-4 text-apple-blue" />
        <p className="text-xs uppercase tracking-[0.18em]">{label}</p>
      </div>
      <p className="text-sm font-semibold text-ink">{value}</p>
    </div>
  );
}

function InfoBlock({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="mb-1 text-xs font-semibold uppercase tracking-[0.18em] text-ink-faint">{label}</dt>
      <dd className="text-sm text-ink">{value}</dd>
    </div>
  );
}
