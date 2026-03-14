'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { Loader2, Plus } from 'lucide-react';

import { PageHeader } from '@/components/page-header';
import { PageShell } from '@/components/page-shell';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import {
  createCampaign,
  fetchCampaigns,
  generateCampaignContent,
} from '@/lib/api';
import type { Campaign } from '@/lib/types';
import { SOCIAL_PLATFORMS } from '@/lib/types';

const SOCIAL_PLATFORM_LABELS: Record<string, string> = {
  linkedin: 'LinkedIn',
  instagram: 'Instagram',
  twitter: 'X (Twitter)',
  facebook: 'Facebook',
  youtube: 'YouTube',
};

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generatingId, setGeneratingId] = useState<number | null>(null);
  const [piecesCreatedByCampaign, setPiecesCreatedByCampaign] = useState<
    Record<number, number>
  >({});

  const sortedCampaigns = useMemo(
    () =>
      [...campaigns].sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      ),
    [campaigns]
  );

  async function loadCampaigns() {
    setLoading(true);
    setError(null);
    try {
      const list = await fetchCampaigns();
      setCampaigns(list);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load campaigns');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadCampaigns();
  }, []);

  async function handleGenerateContent(id: number) {
    setGeneratingId(id);
    setError(null);

    try {
      const result = await generateCampaignContent(id) as { pieces_created: number };
      setPiecesCreatedByCampaign((prev) => ({
        ...prev,
        [id]: result.pieces_created,
      }));
      await loadCampaigns();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to generate campaign content'
      );
    } finally {
      setGeneratingId(null);
    }
  }

  return (
    <PageShell>
      <PageHeader
        title="Campaigns"
        description="Create campaign plans and generate pre/during/post content"
      >
        <Button asChild>
          <Link href="/dashboard/campaigns/create">
            <Plus className="mr-2 h-4 w-4" />
            New Campaign
          </Link>
        </Button>
      </PageHeader>

      <div className="flex flex-col gap-6 px-4 sm:px-6 lg:px-8">
        {error && (
          <div className="rounded-lg border border-ember/30 bg-ember/5 px-4 py-3 text-sm text-ember">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center gap-2 py-12 text-sm text-ink-soft">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading campaigns...
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {sortedCampaigns.map((campaign) => (
              <Card
                key={campaign.id}
                className="border-white/[0.06] bg-card transition-colors hover:border-apple-blue/20"
              >
                <CardHeader className="flex flex-row items-start justify-between gap-2 pb-2">
                  <h3 className="font-semibold text-ink">
                    {campaign.title || 'Untitled campaign'}
                  </h3>
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      campaign.status === 'draft'
                        ? 'border border-white/[0.08] bg-white/[0.04] text-ink-soft'
                        : campaign.status === 'active'
                          ? 'border border-moss/30 bg-moss/10 text-moss'
                          : 'border border-apple-blue/20 bg-apple-blue/10 text-apple-blue'
                    }`}
                  >
                    {campaign.status}
                  </span>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex flex-wrap items-center gap-2 text-xs text-ink-faint">
                    <span>{campaign.platform_entity}</span>
                    <span>•</span>
                    <span>{campaign.goal || 'No goal'}</span>
                    {campaign.event_date && (
                      <>
                        <span>•</span>
                        <span>
                          {new Date(campaign.event_date).toLocaleDateString()}
                        </span>
                      </>
                    )}
                  </div>

                  {campaign.platforms && campaign.platforms.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {campaign.platforms.map((platform) => (
                        <span
                          key={platform}
                          className="rounded-md border border-white/[0.06] bg-white/[0.04] px-2 py-0.5 text-xs text-ink-soft"
                        >
                          {SOCIAL_PLATFORM_LABELS[platform] || platform}
                        </span>
                      ))}
                    </div>
                  )}

                  {typeof piecesCreatedByCampaign[campaign.id] === 'number' && (
                    <p className="text-xs text-moss">
                      Last run generated {piecesCreatedByCampaign[campaign.id]}{' '}
                      pieces.
                    </p>
                  )}

                  <div className="flex flex-wrap gap-2 pt-2">
                    <Button asChild variant="outline" size="sm">
                      <Link href={`/dashboard/campaigns/${campaign.id}`}>
                        View details
                      </Link>
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleGenerateContent(campaign.id)}
                      disabled={generatingId === campaign.id}
                    >
                      {generatingId === campaign.id ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Generating...
                        </>
                      ) : (
                        'Generate Content'
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}

            {sortedCampaigns.length === 0 && (
              <div className="col-span-full flex flex-col items-center gap-4 rounded-lg border border-dashed border-white/[0.08] bg-white/[0.02] py-16">
                <p className="text-sm text-ink-soft">
                  No campaigns yet. Create one to get started.
                </p>
                <Button asChild>
                  <Link href="/dashboard/campaigns/create">
                    <Plus className="mr-2 h-4 w-4" />
                    New Campaign
                  </Link>
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </PageShell>
  );
}
