'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { Check, Copy, ImageIcon, Loader2, Send, X } from 'lucide-react';

import { ImageGeneratorModal } from '@/components/image-generator/ImageGeneratorModal';
import { PageHeader } from '@/components/page-header';
import { AppSelect } from '@/components/ui/app-select';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { generateAudienceContent, publishToSocial } from '@/lib/api';
import type { AudienceAwarenessStage, AudienceContentResponse } from '@/lib/types';
import { AUDIENCE_STAGES, REGIONS } from '@/lib/types';

const STAGE_LABELS: Record<AudienceAwarenessStage, string> = {
  cold: 'Cold Audience',
  warm: 'Warm Audience',
  hot: 'Hot Audience',
};

const INCOME_BRACKETS = [
  { value: 'low', label: 'Low income' },
  { value: 'middle', label: 'Middle income' },
  { value: 'high', label: 'High income' },
  { value: 'premium', label: 'Premium' },
] as const;

const RESULT_LABELS: Record<string, string> = {
  problem_aware: 'Problem Aware',
  solution_aware: 'Solution Aware',
  objection_handling: 'Objection Handling',
  value: 'Value Content',
  conversion: 'Conversion Focused',
  mixed: 'Mixed Output',
};

const RESULT_ORDER = ['problem_aware', 'solution_aware', 'objection_handling', 'value', 'conversion', 'mixed'];
const HISTORY_STORAGE_KEY = 'wng:audience-content:history:v1';
const HISTORY_LIMIT = 12;

type AudienceHistoryItem = {
  id: string;
  created_at: string;
  audience_type: string;
  region: string;
  income_bracket: string;
  awareness_stage: AudienceAwarenessStage;
  pain_points: string[];
  results: Record<string, string>;
};

function toStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map((item) => String(item)).filter(Boolean);
}

function toResultsMap(value: unknown): Record<string, string> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    if (typeof value === 'string') {
      const parsed = extractJsonObject(value);
      if (parsed && Object.keys(parsed).length > 0) {
        return parsed;
      }
      const stripped = stripCodeFence(value);
      return stripped ? { mixed: stripped } : {};
    }
    return {};
  }

  const row = value as Record<string, unknown>;
  if (row.results !== undefined) {
    const nested = toResultsMap(row.results);
    if (Object.keys(nested).length > 0) {
      return nested;
    }
  }

  return Object.fromEntries(
    Object.entries(row)
      .map(([key, itemValue]) => [key, String(itemValue ?? '')])
      .filter(([, itemValue]) => itemValue.trim().length > 0),
  );
}

function extractHistoryResults(row: Record<string, unknown>): Record<string, string> {
  const candidates: unknown[] = [
    row.results,
    row.result,
    row.output,
    row.outputs,
    row.response,
    row.generated,
    row.data,
  ];

  for (const candidate of candidates) {
    const parsed = toResultsMap(candidate);
    if (Object.keys(parsed).length > 0) {
      return parsed;
    }
  }

  return {};
}

function coerceHistoryItem(value: unknown, fallbackIndex: number): AudienceHistoryItem | null {
  if (!value || typeof value !== 'object') return null;
  const row = value as Record<string, unknown>;

  const awareness = String(row.awareness_stage || 'warm') as AudienceAwarenessStage;
  const awareness_stage: AudienceAwarenessStage =
    awareness === 'cold' || awareness === 'warm' || awareness === 'hot' ? awareness : 'warm';

  return {
    id: String(row.id || `history-${Date.now()}-${fallbackIndex}`),
    created_at: String(row.created_at || new Date().toISOString()),
    audience_type: String(row.audience_type || 'audience'),
    region: String(row.region || 'global'),
    income_bracket: String(row.income_bracket || 'middle'),
    awareness_stage,
    pain_points: toStringArray(row.pain_points),
    results: extractHistoryResults(row),
  };
}

function titleize(value: string) {
  return value
    .split('_')
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(' ');
}

function sortResultEntries(entries: [string, string][]) {
  return entries.sort(([leftKey], [rightKey]) => {
    const leftIndex = RESULT_ORDER.indexOf(leftKey);
    const rightIndex = RESULT_ORDER.indexOf(rightKey);
    const normalizedLeft = leftIndex === -1 ? Number.MAX_SAFE_INTEGER : leftIndex;
    const normalizedRight = rightIndex === -1 ? Number.MAX_SAFE_INTEGER : rightIndex;
    if (normalizedLeft === normalizedRight) {
      return leftKey.localeCompare(rightKey);
    }
    return normalizedLeft - normalizedRight;
  });
}

function stripCodeFence(value: string) {
  const fencedMatch = value.match(/```(?:json)?\s*([\s\S]*?)\s*```/i);
  if (fencedMatch) {
    return fencedMatch[1].trim();
  }
  return value.trim();
}

function extractJsonObject(text: string): Record<string, string> | null {
  const raw = text.trim();
  if (!raw) {
    return null;
  }

  const stripped = stripCodeFence(raw);
  const firstCurly = stripped.indexOf('{');
  const lastCurly = stripped.lastIndexOf('}');
  const candidate =
    firstCurly !== -1 && lastCurly !== -1 && lastCurly > firstCurly
      ? stripped.slice(firstCurly, lastCurly + 1)
      : stripped;

  try {
    const parsed = JSON.parse(candidate);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      return null;
    }
    return Object.fromEntries(
      Object.entries(parsed)
        .filter(([key]) => Boolean(key))
        .map(([key, value]) => [key, typeof value === 'string' ? value.trim() : String(value)]),
    );
  } catch {
    return null;
  }
}

function normalizeAudienceResults(results: Record<string, string> | undefined): Record<string, string> {
  const normalizedEntries = new Map<string, string>();

  for (const [key, rawValue] of Object.entries(results || {})) {
    const value = String(rawValue || '').trim();
    if (!value) {
      continue;
    }

    if (key === 'mixed') {
      const parsedObject = extractJsonObject(value);
      if (parsedObject) {
        for (const [nestedKey, nestedValue] of Object.entries(parsedObject)) {
          const cleaned = stripCodeFence(String(nestedValue));
          if (cleaned) {
            normalizedEntries.set(nestedKey, cleaned);
          }
        }
        continue;
      }
    }

    normalizedEntries.set(key, stripCodeFence(value));
  }

  return Object.fromEntries(sortResultEntries(Array.from(normalizedEntries.entries())));
}

const SOCIAL_PLATFORM_OPTIONS = [
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'twitter', label: 'X / Twitter' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'facebook', label: 'Facebook' },
];

function ApprovePublishInline({ content }: { content: string }) {
  const [open, setOpen] = useState(false);
  const [platform, setPlatform] = useState('linkedin');
  const [imageUrl, setImageUrl] = useState('');
  const [posting, setPosting] = useState(false);
  const [outcome, setOutcome] = useState<'posted' | 'failed' | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (outcome === 'posted') {
    return <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-400"><Check size={11} /> Posted!</span>;
  }
  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="flex h-7 items-center gap-1 rounded-md border border-white/[0.06] bg-white/[0.03] px-2 text-[11px] text-ink-faint transition hover:border-apple-blue/30 hover:bg-apple-blue/10 hover:text-apple-blue"
      >
        <Send size={11} /> Approve & Publish
      </button>
    );
  }
  return (
    <div className="flex flex-wrap items-center gap-1.5 w-full">
      <select
        value={platform}
        onChange={(e) => setPlatform(e.target.value)}
        className="h-7 rounded-md border border-white/[0.08] bg-surface-2 px-2 text-[11px] text-ink focus:border-apple-blue/30 focus:outline-none"
      >
        {SOCIAL_PLATFORM_OPTIONS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
      </select>
      <input
        type="url"
        value={imageUrl}
        onChange={(e) => setImageUrl(e.target.value)}
        placeholder="Image URL (optional)"
        className="h-7 flex-1 min-w-[140px] rounded-md border border-white/[0.08] bg-surface-2 px-2 text-[11px] text-ink placeholder-ink-faint focus:border-apple-blue/30 focus:outline-none"
      />
      <button
        type="button"
        disabled={posting}
        onClick={async () => {
          setPosting(true);
          setError(null);
          try {
            await publishToSocial(content, platform, imageUrl || undefined);
            setOutcome('posted');
            setOpen(false);
          } catch (err) {
            setOutcome('failed');
            setError(err instanceof Error ? err.message : 'Failed');
          } finally {
            setPosting(false);
          }
        }}
        className="flex h-7 items-center gap-1 rounded-md border border-apple-blue/30 bg-apple-blue/10 px-2 text-[11px] text-apple-blue transition hover:bg-apple-blue/20 disabled:opacity-50"
      >
        {posting ? <Loader2 size={11} className="animate-spin" /> : <Check size={11} />} Post Now
      </button>
      <button type="button" onClick={() => setOpen(false)} className="text-ink-faint hover:text-ink"><X size={12} /></button>
      {outcome === 'failed' && <span className="w-full text-[10px] text-red-400">{error ?? 'Failed'}</span>}
    </div>
  );
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

export default function AudienceContentPage() {
  const [audienceType, setAudienceType] = useState('founders');
  const [region, setRegion] = useState<string>('global');
  const [incomeBracket, setIncomeBracket] = useState<string>('middle');
  const [awarenessStage, setAwarenessStage] = useState<AudienceAwarenessStage>('warm');
  const [painPointsInput, setPainPointsInput] = useState('low engagement, inconsistent leads');
  const [result, setResult] = useState<AudienceContentResponse | null>(null);
  const [history, setHistory] = useState<AudienceHistoryItem[]>([]);
  const [selectedHistoryId, setSelectedHistoryId] = useState<string | null>(null);
  const [historyLoaded, setHistoryLoaded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [imageModal, setImageModal] = useState<{ open: boolean; content: string } | null>(null);
  const generatedOutputsRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      const raw = window.localStorage.getItem(HISTORY_STORAGE_KEY);
      if (!raw) {
        setHistoryLoaded(true);
        return;
      }
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        const safeItems = parsed
          .map((item, index) => coerceHistoryItem(item, index))
          .filter((item): item is AudienceHistoryItem => item !== null)
          .slice(0, HISTORY_LIMIT);
        setHistory(safeItems);
      }
    } catch {
      // Ignore storage parse errors; continue with empty state.
    } finally {
      setHistoryLoaded(true);
    }
  }, []);

  useEffect(() => {
    if (!historyLoaded || typeof window === 'undefined') return;
    window.localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history));
  }, [history, historyLoaded]);

  async function handleGenerate() {
    const trimmedAudienceType = audienceType.trim();
    const painPoints = painPointsInput
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);

    if (!trimmedAudienceType) {
      setError('Please enter an audience type.');
      return;
    }
    if (painPoints.length === 0) {
      setError('Please enter at least one pain point.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await generateAudienceContent({
        audience_type: trimmedAudienceType,
        region,
        income_bracket: incomeBracket,
        awareness_stage: awarenessStage,
        pain_points: painPoints,
      });
      const normalizedResult = normalizeAudienceResults(res.results);
      setResult({ results: normalizedResult });

      const historyItem: AudienceHistoryItem = {
        id: `${Date.now()}`,
        created_at: new Date().toISOString(),
        audience_type: trimmedAudienceType,
        region,
        income_bracket: incomeBracket,
        awareness_stage: awarenessStage,
        pain_points: painPoints,
        results: normalizedResult,
      };

      setHistory((previous) => [historyItem, ...previous].slice(0, HISTORY_LIMIT));
      setSelectedHistoryId(historyItem.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate audience content');
    } finally {
      setLoading(false);
    }
  }

  function loadHistoryItem(item: AudienceHistoryItem) {
    const normalized = normalizeAudienceResults(item.results);
    setAudienceType(item.audience_type);
    setRegion(item.region);
    setIncomeBracket(item.income_bracket);
    setAwarenessStage(item.awareness_stage);
    setPainPointsInput((item.pain_points || []).join(', '));
    setSelectedHistoryId(item.id);
    setResult({ results: normalized });
    if (Object.keys(normalized).length === 0) {
      setError('No saved output found for this history item.');
      return;
    }
    setError(null);
    window.setTimeout(() => {
      generatedOutputsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 60);
  }

  function clearHistory() {
    setHistory([]);
    setSelectedHistoryId(null);
  }

  const resultEntries = useMemo(
    () => (result ? Object.entries(normalizeAudienceResults(result.results || {})) : []),
    [result],
  );

  return (
    <div className="flex flex-col gap-6 p-4 sm:p-6">
      <PageHeader
        title="Audience Content"
        description="Generate audience-stage content with explicit audience, region, and pain-point inputs"
      />

      <section className="rounded-lg border bg-card p-5 text-card-foreground shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-ink">Configuration</h2>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-ink">Audience type</label>
            <Input
              value={audienceType}
              onChange={(event) => setAudienceType(event.target.value)}
              placeholder="e.g. founders, coaches, SaaS owners"
              disabled={loading}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-ink">Region</label>
            <AppSelect
              value={region}
              onValueChange={setRegion}
              disabled={loading}
              options={REGIONS.map((value) => ({ value, label: value.toUpperCase() }))}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-ink">Income bracket</label>
            <AppSelect
              value={incomeBracket}
              onValueChange={setIncomeBracket}
              disabled={loading}
              options={INCOME_BRACKETS.map((item) => ({ value: item.value, label: item.label }))}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-ink">Awareness stage</label>
            <AppSelect
              value={awarenessStage}
              onValueChange={(value) => setAwarenessStage(value as AudienceAwarenessStage)}
              disabled={loading}
              options={AUDIENCE_STAGES}
            />
          </div>

          <div className="md:col-span-2">
            <label className="mb-1.5 block text-sm font-medium text-ink">Pain points (comma-separated)</label>
            <Textarea
              className="min-h-[100px] resize-y"
              value={painPointsInput}
              onChange={(event) => setPainPointsInput(event.target.value)}
              placeholder="e.g. low engagement, poor lead quality, unclear messaging"
              disabled={loading}
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
            'Generate Audience Content'
          )}
        </Button>
      </section>

      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {resultEntries.length > 0 && (
        <section ref={generatedOutputsRef} className="rounded-lg border bg-card p-5 text-card-foreground shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-ink">Generated outputs</h2>
          <div className="grid gap-4 lg:grid-cols-2">
            {resultEntries.map(([key, value]) => (
              <article key={key} className="rounded-xl border border-white/[0.06] bg-surface-2 p-4">
                <div className="mb-3 flex items-center justify-between gap-2">
                  <span className="inline-flex rounded-full bg-ember/20 px-2.5 py-0.5 text-xs font-semibold text-ember">
                    {RESULT_LABELS[key] || titleize(key)}
                  </span>
                  <div className="flex flex-wrap items-center gap-1.5">
                    <ApprovePublishInline content={value} />
                    <button
                      type="button"
                      onClick={() => setImageModal({ open: true, content: value })}
                      className="flex h-7 items-center gap-1 rounded-md border border-white/[0.06] bg-white/[0.03] px-2 text-[11px] text-ink-faint transition hover:border-apple-blue/30 hover:bg-apple-blue/10 hover:text-apple-blue"
                    >
                      <ImageIcon size={11} /> Image
                    </button>
                    <CopyButton text={value} />
                  </div>
                </div>
                <p className="whitespace-pre-wrap text-sm text-ink">{value}</p>
              </article>
            ))}
          </div>
        </section>
      )}

      {result && resultEntries.length === 0 && !loading && (
        <p className="text-sm text-ink-soft">No outputs returned. Try refining the inputs.</p>
      )}

      <section className="rounded-lg border bg-card p-5 text-card-foreground shadow-sm">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-lg font-semibold text-ink">Previously generated</h2>
          {history.length > 0 && (
            <Button type="button" variant="outline" size="sm" onClick={clearHistory}>
              Clear history
            </Button>
          )}
        </div>

        {history.length === 0 ? (
          <p className="text-sm text-ink-soft">No previous generations yet. Run once to build your list.</p>
        ) : (
          <div className="grid gap-3">
            {history.map((item) => (
              <article key={item.id} className="rounded-xl border border-white/[0.06] bg-surface-2 p-4">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="font-medium text-ink">{item.audience_type}</p>
                    <p className="text-xs text-ink-soft">
                      {item.region.toUpperCase()} · {titleize(item.income_bracket)} · {STAGE_LABELS[item.awareness_stage]}
                    </p>
                    <p className="mt-1 text-xs text-ink-faint">{new Date(item.created_at).toLocaleString()}</p>
                  </div>

                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="shrink-0 border-apple-blue/30 bg-apple-blue/10 text-apple-blue hover:bg-apple-blue/20"
                    onClick={() => loadHistoryItem(item)}
                  >
                    {selectedHistoryId === item.id ? 'Output loaded' : 'View output'}
                  </Button>
                </div>

                {item.pain_points.length > 0 && (
                  <p className="mt-2 line-clamp-2 text-xs text-ink-soft">
                    Pain points: {item.pain_points.join(', ')}
                  </p>
                )}

                {selectedHistoryId === item.id && Object.keys(normalizeAudienceResults(item.results)).length > 0 && (
                  <div className="mt-3 grid gap-2 md:grid-cols-2">
                    {Object.entries(normalizeAudienceResults(item.results)).map(([key, value]) => (
                      <div key={`${item.id}-${key}`} className="rounded-md border border-white/[0.06] bg-surface-3 p-2.5">
                        <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-apple-blue/80">
                          {RESULT_LABELS[key] || titleize(key)}
                        </p>
                        <p className="mt-1 line-clamp-3 text-xs text-ink-soft">{value}</p>
                      </div>
                    ))}
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </section>

      {imageModal && (
        <ImageGeneratorModal
          open={imageModal.open}
          onOpenChange={(open) => setImageModal((s) => s ? { ...s, open } : null)}
          content={imageModal.content}
          platform="instagram"
        />
      )}
    </div>
  );
}
