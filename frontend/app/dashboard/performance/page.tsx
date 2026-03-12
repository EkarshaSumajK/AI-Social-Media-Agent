'use client';

import { BarChart3, Lightbulb, Loader2, Target } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { PageHeader } from '@/components/page-header';
import { fetchPerformance, fetchPerformanceInsights } from '@/lib/api';
import type { PerformanceInsight, PerformanceMetric, PerformanceMetrics } from '@/lib/types';

function MetricCard({ metric }: { metric: PerformanceMetric }) {
  return (
    <div className="flex items-center gap-4 rounded-lg border bg-card p-4 text-card-foreground shadow-sm">
      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-apple-blue/10 text-apple-blue">
        <BarChart3 className="h-5 w-5" />
      </div>
      <div>
        <p className="text-2xl font-bold text-ink">{metric.value}</p>
        <p className="text-xs text-ink-soft">{metric.metric.replace(/_/g, ' ')}</p>
        {metric.change_pct != null && (
          <p className="text-[11px] text-ink-faint">Change: {metric.change_pct}%</p>
        )}
      </div>
    </div>
  );
}

const RECOMMENDATION_PHRASES = /^(we\s+)?(recommend|suggest|consider|try|focus|prioritise|prioritize)/i;

function parseInsights(value: string): string[] {
  const lines = value.split('\n');
  const items: string[] = [];
  let inInsights = false;
  let hitRecommendations = false;

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    if (/^##\s*insights/i.test(trimmed)) {
      inInsights = true;
      hitRecommendations = false;
      continue;
    }
    if (/^##\s*recommendations/i.test(trimmed)) {
      hitRecommendations = true;
      inInsights = false;
      continue;
    }
    if (hitRecommendations) continue;
    if (!inInsights && hitRecommendations) continue;
    const isBullet = /^[-*•]/.test(trimmed) || /^\d+[.)]\s/.test(trimmed);
    if (!isBullet && !inInsights) continue;
    const cleaned = trimmed.replace(/^[-*\d.)•]\s*/, '').trim();
    if (cleaned.length < 10) continue;
    if (RECOMMENDATION_PHRASES.test(cleaned)) continue;
    items.push(cleaned);
  }
  if (items.length > 0) return items;
  const fallback = value
    .split('\n')
    .map((l) => l.trim().replace(/^[-*\d.)•]\s*/, ''))
    .filter((l) => l.length > 15 && !l.startsWith('##') && !RECOMMENDATION_PHRASES.test(l));
  return fallback.length > 0 ? fallback : (value.trim() ? [value.trim()] : []);
}

export default function PerformancePage() {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [insights, setInsights] = useState<PerformanceInsight | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [metricData, insightData] = await Promise.all([
          fetchPerformance(),
          fetchPerformanceInsights(),
        ]);
        setMetrics(metricData);
        setInsights(insightData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load performance data');
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  const parsedInsights = useMemo(() => parseInsights(insights?.insights || ''), [insights]);

  if (loading) {
    return (
      <div className="flex flex-col gap-6 p-4 sm:p-6">
        <PageHeader title="Performance Analytics" description="Track performance metrics and AI guidance" />
        <div className="flex items-center gap-2 text-sm text-ink-soft">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading performance data...
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 p-4 sm:p-6">
      <PageHeader title="Performance Analytics" description="Track performance metrics and AI guidance" />

      {error && (
        <div className="rounded-xl border border-ember/30 bg-ember/5 px-4 py-3 text-sm text-ember">
          {error}
        </div>
      )}

      {metrics && (
        <>
          <section>
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-lg font-semibold text-ink">Metrics</h2>
              <p className="text-xs text-ink-soft">
                Window: {metrics.days} days {metrics.platform ? `· Platform: ${metrics.platform}` : '· All platforms'}
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {(metrics.metrics || []).map((metric) => (
                <MetricCard key={metric.metric} metric={metric} />
              ))}
            </div>

            {(!metrics.metrics || metrics.metrics.length === 0) && (
              <p className="text-sm text-ink-soft">No metrics available.</p>
            )}
          </section>

          {insights && (
            <div className="grid gap-6 lg:grid-cols-2">
              {(parsedInsights.length > 0 || insights.insights?.trim()) && (
                <section className="rounded-lg border bg-card p-5 text-card-foreground shadow-sm">
                  <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-ink">
                    <Lightbulb className="h-5 w-5 text-apple-blue" />
                    AI Insights
                  </h2>
                  {parsedInsights.length > 0 ? (
                    <ul className="space-y-2">
                      {parsedInsights.map((item, index) => (
                        <li key={index} className="flex items-start gap-2 text-sm text-ink">
                          <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-apple-blue" />
                          {item}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="whitespace-pre-wrap text-sm text-ink">{insights.insights?.trim()}</p>
                  )}
                </section>
              )}

              {(Array.isArray(insights.recommendations) && insights.recommendations.length > 0) && (
                <section className="rounded-lg border bg-card p-5 text-card-foreground shadow-sm">
                  <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-ink">
                    <Target className="h-5 w-5 text-moss" />
                    Recommendations
                  </h2>
                  <ul className="space-y-2">
                    {insights.recommendations.map((item, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm text-ink">
                        <span className="mt-1.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded bg-moss/20 text-xs font-bold text-moss">
                          {index + 1}
                        </span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {parsedInsights.length === 0 && !insights.insights?.trim() && (!insights.recommendations?.length) && (
                <p className="col-span-2 text-sm text-ink-soft">
                  No insights generated yet. Ensure LLM_API_KEY is set and try refreshing.
                </p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
