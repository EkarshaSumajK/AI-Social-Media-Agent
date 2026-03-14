'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { AppSelect } from '@/components/ui/app-select';
import { Loader2, ExternalLink, Zap, Filter } from 'lucide-react';

import { PageHeader } from '@/components/page-header';
import { StatusBadge } from '@/components/status-badge';
import { collectTopics, fetchDraftTaskStatus, fetchTopics, generateDraft } from '@/lib/api';
import type { DraftTaskStatusResponse, Topic } from '@/lib/types';
import { TOPIC_CATEGORIES, REGIONS } from '@/lib/types';

const DRAFT_STAGE_LABELS: Record<string, string> = {
  queued: 'Queued',
  loading_topic: 'Loading topic details',
  screening_article: 'Screening relevance',
  duplicate_check: 'Checking duplicates',
  enrichment: 'Enriching context',
  draft_generation: 'Generating draft',
  quality_guard: 'Running quality checks',
  saving: 'Saving draft',
  completed: 'Completed',
  failed: 'Failed',
};

export default function TopicsPage() {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activity, setActivity] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<'today' | '48h' | 'week' | 'all'>('today');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [regionFilter, setRegionFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [busyTopicId, setBusyTopicId] = useState<number | null>(null);
  const [draftProgress, setDraftProgress] = useState<{
    taskId: string; stage: string; progress: number; message: string; active: boolean;
  } | null>(null);
  const pollingRef = useRef<Set<string>>(new Set());

  async function loadTopics() {
    setLoading(true);
    try {
      const data = await fetchTopics({ since: timeRange });
      setTopics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load topics');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadTopics(); }, [timeRange]);

  const filtered = useMemo(() => {
    let result = topics;
    if (categoryFilter !== 'all') {
      result = result.filter((t) => t.topic_category === categoryFilter);
    }
    if (regionFilter !== 'all') {
      result = result.filter((t) => t.region === regionFilter);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter((t) => t.title.toLowerCase().includes(q) || t.summary?.toLowerCase().includes(q));
    }
    return result;
  }, [topics, categoryFilter, regionFilter, searchQuery]);

  async function handleCollect() {
    setPipelineRunning(true);
    setError(null);
    try {
      const result = await collectTopics();
      setActivity(`Fetched ${result.fetched}, stored ${result.stored}, X topics ${result.x_topics_found}`);
      await loadTopics();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Collection failed');
    } finally {
      setPipelineRunning(false);
    }
  }

  async function handleGenerate(topicId: number) {
    setBusyTopicId(topicId);
    setError(null);
    try {
      const result = await generateDraft(topicId, true);
      setActivity(result.message);
      if (result.task_id) {
        setDraftProgress({ taskId: result.task_id, stage: 'Queued', progress: 5, message: result.message, active: true });
        monitorTask(result.task_id);
      }
      await loadTopics();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed');
    } finally {
      setBusyTopicId(null);
    }
  }

  async function monitorTask(taskId: string) {
    if (pollingRef.current.has(taskId)) return;
    pollingRef.current.add(taskId);
    try {
      for (let i = 0; i < 120; i++) {
        await new Promise((r) => setTimeout(r, 3000));
        const task: DraftTaskStatusResponse = await fetchDraftTaskStatus(taskId);
        const stageKey = (task.stage || '').toLowerCase();
        const stage = DRAFT_STAGE_LABELS[stageKey] || 'Processing';
        const progress = task.progress ?? 20;
        const status = (task.status || '').toLowerCase();
        setDraftProgress({ taskId, stage, progress, message: task.message, active: status === 'queued' || status === 'running' });
        if (status && status !== 'queued' && status !== 'running') {
          setActivity(task.message);
          await loadTopics();
          return;
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Task polling failed');
    } finally {
      pollingRef.current.delete(taskId);
    }
  }

  return (
    <div className="flex flex-col">
      <PageHeader title="Topics Pipeline" description="Screened trending topics from X, news, and trusted sources">
        <Button onClick={handleCollect} disabled={pipelineRunning}>
          {pipelineRunning ? <><Loader2 size={14} className="mr-1.5 animate-spin" /> Collecting...</> : <><Zap size={14} className="mr-1.5" /> Run Pipeline</>}
        </Button>
      </PageHeader>

      <div className="flex flex-col gap-4 p-4 sm:p-6">
        {activity && <div className="rounded-xl bg-emerald-500/10 border border-emerald-500/20 px-4 py-2.5 text-sm text-emerald-400">{activity}</div>}
        {error && <div className="rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-2.5 text-sm text-red-400">{error}</div>}

        {draftProgress?.active && (
          <div className="rounded-lg border bg-card text-card-foreground shadow-sm p-4">
            <div className="mb-2 flex items-center justify-between text-sm">
              <span className="font-medium text-ink">{draftProgress.stage}</span>
              <span className="text-ink-soft">{Math.round(draftProgress.progress)}%</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-white/[0.08]">
              <div className="h-full rounded-full bg-apple-blue transition-all" style={{ width: `${draftProgress.progress}%` }} />
            </div>
            <p className="mt-1.5 text-xs text-ink-soft">{draftProgress.message}</p>
          </div>
        )}

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex w-full items-center gap-1.5 sm:w-auto">
            <Filter size={14} className="text-ink-faint" />
            <Input
              className="w-full sm:w-60"
              placeholder="Search topics..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div className="flex w-full items-center overflow-hidden rounded-xl border border-white/[0.06] bg-surface-2 text-xs sm:w-auto">
            {(['today', '48h', 'week', 'all'] as const).map((r) => (
              <Button
                key={r}
                type="button"
                variant="ghost"
                className={`px-3 py-1.5 capitalize ${timeRange === r ? 'bg-apple-blue/10 font-semibold text-ink' : 'text-ink-soft hover:text-ink'}`}
                onClick={() => setTimeRange(r)}
              >
                {r === '48h' ? '48h' : r === 'all' ? 'All' : r === 'today' ? 'Today' : 'Week'}
              </Button>
            ))}
          </div>

          <AppSelect
            value={categoryFilter}
            onValueChange={setCategoryFilter}
            triggerClassName="w-full sm:w-40"
            options={[
              { value: 'all', label: 'All Categories' },
              ...TOPIC_CATEGORIES.map((category) => ({
                value: category,
                label: category.replace('_', ' '),
              })),
            ]}
          />

          <AppSelect
            value={regionFilter}
            onValueChange={setRegionFilter}
            triggerClassName="w-full sm:w-32"
            options={[
              { value: 'all', label: 'All Regions' },
              ...REGIONS.map((region) => ({ value: region, label: region })),
            ]}
          />

          <span className="text-xs text-ink-soft">{filtered.length} topics</span>
        </div>

        {loading ? (
          <div className="flex items-center gap-2 py-12 text-sm text-ink-soft"><Loader2 size={16} className="animate-spin" /> Loading topics...</div>
        ) : (
          <div className="space-y-3">
            {filtered.map((topic) => (
              <div key={topic.id} className="rounded-lg border bg-card text-card-foreground shadow-sm p-4">
                <div className="mb-2 flex flex-wrap items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    {topic.x_trend_phrase && (
                      <div className="mb-1.5 flex items-center gap-1.5">
                        <span className="inline-flex items-center gap-1 rounded-md bg-slate-900 px-2 py-0.5 text-[11px] font-semibold text-white">X Trend</span>
                        <span className="text-xs text-ink-soft">{topic.x_trend_phrase}</span>
                      </div>
                    )}
                    <p className="font-semibold text-ink">{topic.title}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={topic.status} />
                    {topic.topic_category && (
                      <span className="rounded-md bg-surface-3 px-2 py-0.5 text-[11px] font-medium text-ink-soft">{topic.topic_category.replace('_', ' ')}</span>
                    )}
                  </div>
                </div>

                <div className="mb-2 flex flex-wrap items-center gap-2">
                  {topic.is_trending && (
                    <span className="rounded-full bg-apple-blue/10 border border-apple-blue/20 px-2.5 py-0.5 text-xs font-semibold text-apple-blue">Trending</span>
                  )}
                  <span className="rounded-full bg-surface-2 border border-white/[0.06] px-2.5 py-0.5 text-xs text-ink-soft">{topic.region}</span>
                  <span className="rounded-full bg-apple-blue/10 border border-apple-blue/20 px-2.5 py-0.5 text-xs text-apple-blue">{topic.platform}</span>
                  <span className="text-xs text-ink-soft">Trust: {topic.trust_score}/100</span>
                  <span className="text-xs text-ink-soft">Relevance: {topic.relevance_score}/100</span>
                </div>

                {topic.summary && <p className="mb-2 line-clamp-2 text-sm text-ink-soft">{topic.summary}</p>}

                <div className="flex items-center gap-3 text-xs">
                  <span className="text-ink-soft">{topic.source_name || 'Source'} | {new Date(topic.created_at).toLocaleString()}</span>
                  <a className="font-medium text-apple-blue/80 hover:text-apple-blue hover:underline" href={topic.source_url} rel="noreferrer" target="_blank">
                    <ExternalLink size={12} className="mr-0.5 inline" /> Source
                  </a>
                  {topic.status === 'new' && (
                    <Button className="!py-1 !text-xs" onClick={() => handleGenerate(topic.id)} disabled={busyTopicId === topic.id}>
                      {busyTopicId === topic.id ? 'Queuing...' : 'Generate Draft'}
                    </Button>
                  )}
                </div>
              </div>
            ))}
            {filtered.length === 0 && <p className="py-8 text-center text-sm text-ink-soft">No topics found for the selected filters.</p>}
          </div>
        )}
      </div>
    </div>
  );
}
