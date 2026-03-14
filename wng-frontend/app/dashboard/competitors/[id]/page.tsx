'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ArrowLeft, ExternalLink, Loader2, Search } from 'lucide-react';

import { CompetitorAnalysisRenderer } from '@/components/competitor-analysis-renderer';
import { PageHeader } from '@/components/page-header';
import { PageShell } from '@/components/page-shell';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { analyzeCompetitor, fetchCompetitor, fetchCompetitorAnalyses } from '@/lib/api';
import type { Competitor, CompetitorAnalysisStored } from '@/lib/types';

const SOCIAL_PLATFORM_LABELS: Record<string, string> = {
  linkedin: 'LinkedIn',
  instagram: 'Instagram',
  twitter: 'X (Twitter)',
  facebook: 'Facebook',
  youtube: 'YouTube',
};

function labelizePlatform(value: string) {
  return SOCIAL_PLATFORM_LABELS[value] || value;
}

export default function CompetitorDetailPage() {
  const params = useParams<{ id: string }>();
  const competitorId = Number(params.id);

  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [competitor, setCompetitor] = useState<Competitor | null>(null);
  const [storedAnalysis, setStoredAnalysis] = useState<CompetitorAnalysisStored | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [comp, analyses] = await Promise.all([
          fetchCompetitor(competitorId),
          fetchCompetitorAnalyses(competitorId),
        ]);
        setCompetitor(comp ?? null);
        setStoredAnalysis(analyses.length > 0 ? analyses[0] : null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load competitor');
      } finally {
        setLoading(false);
      }
    }

    if (Number.isNaN(competitorId)) {
      setLoading(false);
      setError('Invalid competitor id');
      return;
    }

    void load();
  }, [competitorId]);

  async function handleAnalyze() {
    if (!competitor) return;
    setAnalyzing(true);
    setError(null);
    try {
      const result = await analyzeCompetitor(competitor.id);
      setStoredAnalysis({
        id: result.id,
        competitor_id: result.competitor_id,
        analysis: result.analysis,
        created_at: result.created_at,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze competitor');
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <PageShell>
      <PageHeader
        title={competitor?.name ?? 'Competitor'}
        description="Track competitor and run deep analysis"
      >
        <Button asChild variant="outline" size="sm">
          <Link href="/dashboard/competitors">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to list
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
            Loading competitor...
          </div>
        ) : competitor ? (
          <>
            <Card className="border-white/[0.06] bg-card">
              <CardHeader className="flex flex-row flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-base font-semibold text-ink">{competitor.name}</h2>
                  <p className="mt-1 text-sm text-ink-soft">Platform entity: {competitor.platform_entity}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button asChild variant="outline" size="sm">
                    <a href={competitor.profile_url} target="_blank" rel="noreferrer">
                      <ExternalLink className="mr-2 h-4 w-4" />
                      Open profile
                    </a>
                  </Button>
                  <Button type="button" variant="secondary" size="sm" onClick={handleAnalyze} disabled={analyzing}>
                    {analyzing ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Search className="mr-2 h-4 w-4" />
                        Run analysis
                      </>
                    )}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <dl className="grid gap-3 sm:grid-cols-3">
                  <InfoBlock label="Social Platform" value={labelizePlatform(competitor.platform)} />
                  <InfoBlock label="Created By User ID" value={String(competitor.created_by)} />
                  <InfoBlock label="Profile URL" value={competitor.profile_url} />
                </dl>
              </CardContent>
            </Card>

            <Card className="border-white/[0.06] bg-card">
              <CardHeader className="pb-3">
                <h2 className="text-base font-semibold text-ink">Analysis</h2>
                {storedAnalysis && (
                  <p className="mt-1 text-xs text-ink-faint">
                    Last updated:{' '}
                    {new Date(storedAnalysis.created_at).toLocaleString(undefined, {
                      dateStyle: 'medium',
                      timeStyle: 'short',
                    })}
                  </p>
                )}
              </CardHeader>
              <CardContent>
                {storedAnalysis ? (
                  <CompetitorAnalysisRenderer analysis={storedAnalysis.analysis} />
                ) : (
                  <p className="text-sm text-ink-soft">
                    Run analysis to generate detailed competitor insights.
                  </p>
                )}
              </CardContent>
            </Card>
          </>
        ) : (
          <p className="py-12 text-sm text-ink-soft">Competitor not found.</p>
        )}
      </div>
    </PageShell>
  );
}

function InfoBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-white/[0.06] bg-surface-2 p-3">
      <dt className="mb-1 text-xs font-semibold uppercase tracking-[0.16em] text-ink-faint">{label}</dt>
      <dd className="break-all text-sm text-ink">{value}</dd>
    </div>
  );
}
