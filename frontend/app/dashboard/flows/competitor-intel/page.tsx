'use client';

import { useEffect, useState } from 'react';
import { ChevronDown, ChevronUp, Loader2, Radar, RefreshCw } from 'lucide-react';

import { PageHeader } from '@/components/page-header';
import { CardListSkeleton } from '@/components/skeletons';
import { CompetitorAnalysisRenderer } from '@/components/competitor-analysis-renderer';
import { AppSelect } from '@/components/ui/app-select';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { addCompetitor, analyzeCompetitor, fetchCompetitors } from '@/lib/api';
import type { Competitor, CompetitorAnalysis } from '@/lib/types';
import { PLATFORMS, SOCIAL_PLATFORMS } from '@/lib/types';
import { cn } from '@/lib/utils';

const SOCIAL_PLATFORM_LABELS: Record<string, string> = {
  linkedin: 'LinkedIn',
  instagram: 'Instagram',
  twitter: 'X (Twitter)',
  facebook: 'Facebook',
  youtube: 'YouTube',
};

const PLATFORM_BADGE: Record<string, string> = {
  linkedin: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  twitter: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
  instagram: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
  youtube: 'bg-red-500/10 text-red-400 border-red-500/20',
  facebook: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
};

export default function CompetitorIntelFlowPage() {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState('');
  const [profileUrl, setProfileUrl] = useState('');
  const [platform, setPlatform] = useState('linkedin');
  const [platformEntity, setPlatformEntity] = useState('horizon');
  const [submitting, setSubmitting] = useState(false);
  const [analyzingId, setAnalyzingId] = useState<number | null>(null);
  const [analysisMap, setAnalysisMap] = useState<Record<number, CompetitorAnalysis>>({});
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadCompetitors() {
    setLoading(true);
    try {
      const data = await fetchCompetitors();
      setCompetitors(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void loadCompetitors(); }, []);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() || !profileUrl.trim()) { setError('Name and URL required.'); return; }
    setSubmitting(true);
    setError(null);
    try {
      await addCompetitor({ name: name.trim(), platform, profile_url: profileUrl.trim(), platform_entity: platformEntity });
      setName('');
      setProfileUrl('');
      await loadCompetitors();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleAnalyze(id: number) {
    setAnalyzingId(id);
    setError(null);
    try {
      const result = await analyzeCompetitor(id);
      setAnalysisMap((prev) => ({ ...prev, [id]: result }));
      setExpandedId(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setAnalyzingId(null);
    }
  }

  return (
    <div className="flex flex-col gap-6 p-4 sm:p-6">
      <PageHeader
        title="Competitor Intelligence"
        description="Track competitors and get AI-powered analysis of their content strategy"
        eyebrow="Flow"
      />

      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-400">{error}</div>
      )}

      <div className="grid gap-6 lg:grid-cols-5">
        {/* Add form */}
        <section className="lg:col-span-2 rounded-lg border bg-card p-5 text-card-foreground shadow-sm h-fit">
          <div className="mb-4 flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-apple-blue/15 text-[11px] font-bold text-apple-blue">1</span>
            <h2 className="text-base font-semibold text-ink">Add Competitor</h2>
          </div>

          <form onSubmit={handleAdd} className="grid gap-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink">Name</label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Acme Corp" disabled={submitting} />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink">Profile URL</label>
              <Input type="url" value={profileUrl} onChange={(e) => setProfileUrl(e.target.value)} placeholder="https://..." disabled={submitting} />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink">Platform</label>
              <AppSelect
                value={platform}
                onValueChange={setPlatform}
                disabled={submitting}
                options={SOCIAL_PLATFORMS.map((p) => ({ value: p, label: SOCIAL_PLATFORM_LABELS[p] || p }))}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink">Platform Entity</label>
              <AppSelect
                value={platformEntity}
                onValueChange={setPlatformEntity}
                disabled={submitting}
                options={PLATFORMS.map((p) => ({ value: p.value, label: p.label }))}
              />
            </div>
            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? <><Loader2 size={14} className="mr-2 animate-spin" /> Adding...</> : '+ Track Competitor'}
            </Button>
          </form>
        </section>

        {/* Competitor list */}
        <section className="lg:col-span-3 rounded-lg border bg-card text-card-foreground shadow-sm">
          <div className="flex items-center justify-between gap-3 border-b border-white/[0.06] px-5 py-4">
            <div className="flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-apple-blue/15 text-[11px] font-bold text-apple-blue">2</span>
              <h2 className="text-base font-semibold text-ink">Your Competitors</h2>
            </div>
            <Button variant="ghost" size="sm" onClick={loadCompetitors} disabled={loading}>
              <RefreshCw size={13} className={cn(loading && 'animate-spin')} />
            </Button>
          </div>

          <div className="p-5">
            {loading ? (
              <CardListSkeleton count={3} />
            ) : competitors.length === 0 ? (
              <div className="flex flex-col items-center gap-3 py-8 text-center">
                <Radar size={32} className="text-ink-faint" />
                <p className="text-sm text-ink-soft">No competitors tracked yet. Add one to start.</p>
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {competitors.map((comp) => {
                  const badgeClass = PLATFORM_BADGE[comp.platform] ?? 'bg-white/[0.06] text-ink-soft border-white/[0.08]';
                  const hasAnalysis = Boolean(analysisMap[comp.id]);
                  const isExpanded = expandedId === comp.id;

                  return (
                    <div key={comp.id} className="rounded-xl border border-white/[0.06] bg-surface-2">
                      <div className="flex items-start justify-between gap-3 p-4">
                        <div className="min-w-0 flex-1">
                          <p className="font-semibold text-ink">{comp.name}</p>
                          <a
                            href={comp.profile_url}
                            target="_blank"
                            rel="noreferrer"
                            className="mt-0.5 block truncate text-xs text-apple-blue/70 hover:text-apple-blue hover:underline"
                          >
                            {comp.profile_url}
                          </a>
                          <div className="mt-2 flex flex-wrap gap-2">
                            <span className={cn('rounded-full border px-2.5 py-0.5 text-[11px] font-medium', badgeClass)}>
                              {SOCIAL_PLATFORM_LABELS[comp.platform] || comp.platform}
                            </span>
                          </div>
                        </div>

                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => handleAnalyze(comp.id)}
                          disabled={analyzingId === comp.id}
                          className="flex-shrink-0"
                        >
                          {analyzingId === comp.id ? (
                            <><Loader2 size={13} className="mr-1.5 animate-spin" /> Analyzing...</>
                          ) : (
                            <><Radar size={13} className="mr-1.5" /> {hasAnalysis ? 'Re-Analyze' : 'Analyze'}</>
                          )}
                        </Button>
                      </div>

                      {hasAnalysis && (
                        <div className="border-t border-white/[0.06]">
                          <button
                            type="button"
                            className="flex w-full items-center justify-between px-4 py-2.5 text-left text-xs font-semibold text-apple-blue transition hover:bg-apple-blue/5"
                            onClick={() => setExpandedId(isExpanded ? null : comp.id)}
                          >
                            <span>View Analysis</span>
                            {isExpanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                          </button>

                          {isExpanded && (
                            <div className="px-4 pb-4">
                              <CompetitorAnalysisRenderer analysis={analysisMap[comp.id].analysis} />
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
