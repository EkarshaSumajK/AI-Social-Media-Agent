'use client';

import Link from 'next/link';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';

import { StatusBadge } from '@/components/status-badge';
import { TipTapEditor } from '@/components/tiptap-editor';
import { approveDraft, fetchDraft, publishDraft, publishSocial, rejectDraft, updateDraft } from '@/lib/api';
import type { Article } from '@/lib/types';

interface DraftForm {
  content_html: string;
  seo_title: string;
  meta_description: string;
  keywords: string;
  issue_summary: string;
  why_it_matters: string;
  mental_health_implications: string;
  professional_insight: string;
  how_services_help: string;
  call_to_action: string;
  social_posts: Record<string, string>;
}

type HealthTone = 'good' | 'warn' | 'bad';

interface DraftAnalysis {
  score: number;
  titleLength: number;
  metaLength: number;
  slugLength: number;
  suggestedSlug: string;
  wordCount: number;
  readingTimeMinutes: number;
  sentenceAverageWords: number;
  paragraphAverageWords: number;
  readability: number;
  readingGrade: number;
  primaryKeyword: string | null;
  keywordPlacement: {
    inTitle: boolean;
    inMeta: boolean;
    inIntro: boolean;
    inHeadings: boolean;
  };
  headingCounts: {
    h1: number;
    h2: number;
    h3: number;
  };
  headingStructureValid: boolean;
  headingIssues: string[];
  links: {
    internal: number;
    external: number;
    invalid: number;
  };
  images: {
    total: number;
    withAlt: number;
    altCoverage: number;
  };
  titleScore: number;
  metaScore: number;
  slugScore: number;
  keywordScore: number;
  headingScore: number;
  wordScore: number;
  linkScore: number;
  imageScore: number;
  readabilityScore: number;
  suggestions: string[];
}

const EMPTY_FORM: DraftForm = {
  content_html: '',
  seo_title: '',
  meta_description: '',
  keywords: '',
  issue_summary: '',
  why_it_matters: '',
  mental_health_implications: '',
  professional_insight: '',
  how_services_help: '',
  call_to_action: '',
  social_posts: {
    instagram: '',
    linkedin: '',
    twitter: '',
    facebook: '',
  },
};

export default function DraftDetailPage() {
  const params = useParams<{ id: string }>();
  const draftId = Number(params.id);

  const [draft, setDraft] = useState<Article | null>(null);
  const [form, setForm] = useState<DraftForm>(EMPTY_FORM);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadDraft() {
    setLoading(true);
    setError(null);
    try {
      const article = await fetchDraft(draftId);
      setDraft(article);
      setForm(mapDraftToForm(article));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load draft');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (Number.isNaN(draftId)) {
      setError('Invalid draft ID');
      setLoading(false);
      return;
    }
    loadDraft();
  }, [draftId]);

  const keywords = useMemo(
    () =>
      form.keywords
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean),
    [form.keywords]
  );
  const analysis = useMemo(
    () =>
      analyzeDraft({
        seoTitle: form.seo_title,
        metaDescription: form.meta_description,
        keywords,
        contentHtml: form.content_html,
      }),
    [form.seo_title, form.meta_description, keywords, form.content_html]
  );

  async function handleSave() {
    if (!draft) return;
    setSaving(true);
    setError(null);
    setMessage(null);

    try {
      const payload = {
        content_html: form.content_html,
        seo_title: form.seo_title,
        meta_description: form.meta_description,
        keywords,
        issue_summary: form.issue_summary,
        why_it_matters: form.why_it_matters,
        mental_health_implications: form.mental_health_implications,
        professional_insight: form.professional_insight,
        how_services_help: form.how_services_help,
        call_to_action: form.call_to_action,
        social_posts: form.social_posts,
      };

      const updated = await updateDraft(draft.id, payload as unknown as Partial<Article>);
      setDraft(updated);
      setForm(mapDraftToForm(updated));
      setMessage('Draft saved.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save draft');
    } finally {
      setSaving(false);
    }
  }

  async function handleApprove() {
    if (!draft) return;
    setSaving(true);
    setError(null);

    try {
      const updated = await approveDraft(draft.id);
      setDraft(updated);
      setForm(mapDraftToForm(updated));
      setMessage('Draft approved. Publish is now enabled.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Approval failed');
    } finally {
      setSaving(false);
    }
  }

  async function handleReject() {
    if (!draft) return;
    setSaving(true);
    setError(null);

    try {
      const updated = await rejectDraft(draft.id);
      setDraft(updated);
      setForm(mapDraftToForm(updated));
      setMessage('Draft rejected.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Rejection failed');
    } finally {
      setSaving(false);
    }
  }

  async function handlePublish() {
    if (!draft) return;
    setSaving(true);
    setError(null);

    try {
      const updated = await publishDraft(draft.id);
      setDraft(updated);
      setForm(mapDraftToForm(updated));
      setMessage('Article published. Social worker has been triggered.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Publishing failed');
    } finally {
      setSaving(false);
    }
  }

  async function handlePublishSocial() {
    if (!draft) return;
    setSaving(true);
    setError(null);

    try {
      const result = await publishSocial(draft.id);
      setMessage(`Social publish result: ${JSON.stringify(result.outcomes)}`);
      await loadDraft();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Social publishing failed');
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <main className="p-4 text-sm text-ink-soft sm:p-8">Loading draft...</main>;
  }

  if (!draft) {
    return <main className="p-4 text-sm text-red-400 sm:p-8">Draft not found.</main>;
  }

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-6 md:px-8">
      <section className="rounded-lg border bg-card text-card-foreground shadow-sm p-5">
        <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.25em] text-apple-blue">Editorial Review</p>
            <h1 className="text-3xl font-bold text-ink">{cleanMarkdownText(draft.seo_title)}</h1>
          </div>
          <div className="flex items-center gap-2">
            <StatusBadge status={draft.status} />
            <Link
              href="/dashboard"
              className="inline-flex h-10 items-center justify-center rounded-md border border-white/[0.10] bg-white/[0.06] px-4 py-2 text-sm font-medium text-ink transition-colors hover:bg-white/[0.10]"
            >
              Back to Dashboard
            </Link>
          </div>
        </div>

        {message && <p className="mb-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-3 text-sm text-emerald-400">{message}</p>}
        {error && <p className="mb-3 rounded-xl bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">{error}</p>}

        <div className="grid gap-4 md:grid-cols-2">
          <Field label="SEO Title" value={form.seo_title} onChange={(value) => setForm((prev) => ({ ...prev, seo_title: value }))} />
          <Field
            label="Meta Description"
            value={form.meta_description}
            onChange={(value) => setForm((prev) => ({ ...prev, meta_description: value }))}
          />
        </div>

        <div className="mt-4">
          <label className="mb-1 block text-sm font-medium text-ink-soft">Keywords (comma separated)</label>
          <Input value={form.keywords} onChange={(event) => setForm((prev) => ({ ...prev, keywords: event.target.value }))} />
        </div>
      </section>

      <section className="rounded-lg border bg-card text-card-foreground shadow-sm p-5 draft-body-editor">
        <h2 className="mb-3 text-2xl font-bold text-ink">Article Body (TipTap)</h2>
        <TipTapEditor value={form.content_html} onChange={(value) => setForm((prev) => ({ ...prev, content_html: value }))} />
      </section>

      <section className="rounded-lg border bg-card text-card-foreground shadow-sm grid gap-4 p-5 md:grid-cols-2">
        <TextAreaField
          label="Issue Summary"
          value={form.issue_summary}
          onChange={(value) => setForm((prev) => ({ ...prev, issue_summary: value }))}
        />
        <TextAreaField
          label="Why It Matters"
          value={form.why_it_matters}
          onChange={(value) => setForm((prev) => ({ ...prev, why_it_matters: value }))}
        />
        <TextAreaField
          label="Mental Health Implications"
          value={form.mental_health_implications}
          onChange={(value) => setForm((prev) => ({ ...prev, mental_health_implications: value }))}
        />
        <TextAreaField
          label="Professional Insight"
          value={form.professional_insight}
          onChange={(value) => setForm((prev) => ({ ...prev, professional_insight: value }))}
        />
        <TextAreaField
          label="How Our Services Help"
          value={form.how_services_help}
          onChange={(value) => setForm((prev) => ({ ...prev, how_services_help: value }))}
        />
        <TextAreaField
          label="Call To Action"
          value={form.call_to_action}
          onChange={(value) => setForm((prev) => ({ ...prev, call_to_action: value }))}
        />
      </section>

      <section className="rounded-lg border bg-card text-card-foreground shadow-sm p-5">
        <h2 className="mb-3 text-2xl font-bold text-ink">Social Captions</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {Object.entries(form.social_posts).map(([platform, caption]) => (
            <TextAreaField
              key={platform}
              label={platform}
              value={caption}
              onChange={(value) =>
                setForm((prev) => ({
                  ...prev,
                  social_posts: { ...prev.social_posts, [platform]: value },
                }))
              }
            />
          ))}
        </div>
      </section>

      <section className="rounded-lg border bg-card text-card-foreground shadow-sm p-5">
        <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.25em] text-apple-blue">Pre-Publish Analyzer</p>
            <h2 className="text-2xl font-bold text-ink">Draft Health</h2>
            <p className="text-sm text-ink-soft">Read-only quality and SEO checks from your current draft content.</p>
          </div>
          <div className="flex items-center gap-2">
            <PublishReadinessBadge draft={draft} />
            <ScorePill score={analysis.score} />
          </div>
        </div>

        {/* Backend Quality Metrics — AI Detection, Plagiarism, Structure */}
        <div className="mb-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <AnalyzerMetric
            label="AI Detection"
            value={draft.ai_generated_probability != null ? `${(draft.ai_generated_probability * 100).toFixed(0)}%` : 'N/A'}
            hint={draft.ai_generated_probability != null ? (draft.ai_generated_probability > 0.6 ? 'High AI probability' : draft.ai_generated_probability > 0.3 ? 'Moderate' : 'Looks human') : 'Not yet analyzed'}
            tone={draft.ai_generated_probability != null ? (draft.ai_generated_probability > 0.6 ? 'bad' : draft.ai_generated_probability > 0.3 ? 'warn' : 'good') : 'warn'}
          />
          <AnalyzerMetric
            label="Plagiarism Risk"
            value={draft.source_similarity_score != null ? `${(draft.source_similarity_score * 100).toFixed(0)}%` : 'N/A'}
            hint={draft.source_similarity_score != null ? (draft.source_similarity_score > 0.16 ? 'Above threshold (16%)' : 'Within safe range') : 'Not yet analyzed'}
            tone={draft.source_similarity_score != null ? (draft.source_similarity_score > 0.16 ? 'bad' : draft.source_similarity_score > 0.10 ? 'warn' : 'good') : 'warn'}
          />
          <AnalyzerMetric
            label="Structure Check"
            value={draft.structure_valid ? 'Valid' : 'Issues Found'}
            hint={draft.structure_valid ? 'All 6 required sections present' : 'Missing required sections'}
            tone={draft.structure_valid ? 'good' : 'bad'}
          />
          <AnalyzerMetric
            label="Readability (Server)"
            value={draft.readability_score != null ? `Grade ${draft.readability_score.toFixed(1)}` : 'N/A'}
            hint={draft.readability_score != null ? (draft.readability_score >= 5 && draft.readability_score <= 10 ? 'Target range 5-10' : 'Outside target 5-10') : 'Not yet analyzed'}
            tone={draft.readability_score != null ? (draft.readability_score >= 5 && draft.readability_score <= 10 ? 'good' : 'warn') : 'warn'}
          />
        </div>

        {/* Content Scores — virality, clarity, hook, conversion */}
        {(draft.virality_score != null || draft.clarity_score != null || draft.hook_strength_score != null || draft.conversion_score != null) && (
          <div className="mb-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <AnalyzerMetric
              label="Virality"
              value={draft.virality_score != null ? `${(draft.virality_score * 100).toFixed(0)}%` : 'N/A'}
              hint="Viral potential rating"
              tone={draft.virality_score != null ? toneFromScore(draft.virality_score * 100) : 'warn'}
            />
            <AnalyzerMetric
              label="Clarity"
              value={draft.clarity_score != null ? `${(draft.clarity_score * 100).toFixed(0)}%` : 'N/A'}
              hint="Writing clarity rating"
              tone={draft.clarity_score != null ? toneFromScore(draft.clarity_score * 100) : 'warn'}
            />
            <AnalyzerMetric
              label="Hook Strength"
              value={draft.hook_strength_score != null ? `${(draft.hook_strength_score * 100).toFixed(0)}%` : 'N/A'}
              hint="Opening hook effectiveness"
              tone={draft.hook_strength_score != null ? toneFromScore(draft.hook_strength_score * 100) : 'warn'}
            />
            <AnalyzerMetric
              label="Conversion"
              value={draft.conversion_score != null ? `${(draft.conversion_score * 100).toFixed(0)}%` : 'N/A'}
              hint="CTA effectiveness"
              tone={draft.conversion_score != null ? toneFromScore(draft.conversion_score * 100) : 'warn'}
            />
          </div>
        )}

        {/* Client-side SEO metrics */}
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <AnalyzerMetric label="Word Count" value={String(analysis.wordCount)} hint={`${analysis.readingTimeMinutes} min read · Target 900-1100`} tone={toneFromScore(analysis.wordScore)} />
          <AnalyzerMetric label="SEO Title" value={`${analysis.titleLength} chars`} hint="Target 45-65" tone={toneFromScore(analysis.titleScore)} />
          <AnalyzerMetric
            label="Meta Description"
            value={`${analysis.metaLength} chars`}
            hint="Target 120-160"
            tone={toneFromScore(analysis.metaScore)}
          />
          <AnalyzerMetric label="Slug Length" value={`${analysis.slugLength} chars`} hint={analysis.suggestedSlug || 'No slug yet'} tone={toneFromScore(analysis.slugScore)} />
          <AnalyzerMetric label="Heading Score" value={`${analysis.headingScore}/100`} hint={`H1 ${analysis.headingCounts.h1} | H2 ${analysis.headingCounts.h2} | H3 ${analysis.headingCounts.h3}`} tone={toneFromScore(analysis.headingScore)} />
          <AnalyzerMetric label="Keyword Score" value={`${analysis.keywordScore}/100`} hint={analysis.primaryKeyword || 'Primary keyword not set'} tone={toneFromScore(analysis.keywordScore)} />
          <AnalyzerMetric
            label="Links"
            value={`${analysis.links.internal} internal / ${analysis.links.external} external`}
            hint={analysis.links.invalid > 0 ? `${analysis.links.invalid} invalid URL(s)` : 'No invalid links found'}
            tone={toneFromScore(analysis.linkScore)}
          />
          <AnalyzerMetric
            label="Images Alt Text"
            value={`${analysis.images.withAlt}/${analysis.images.total}`}
            hint={`${analysis.images.altCoverage}% coverage`}
            tone={toneFromScore(analysis.imageScore)}
          />
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div className="rounded-xl border border-white/[0.06] bg-surface-2 p-4">
            <p className="text-sm font-semibold text-ink">Primary Keyword Placement</p>
            <p className="text-xs text-ink-soft">Keyword: {analysis.primaryKeyword || 'Not set'}</p>
            <div className="mt-2 flex flex-wrap gap-2">
              <KeywordChip label="Title" ok={analysis.keywordPlacement.inTitle} />
              <KeywordChip label="Meta" ok={analysis.keywordPlacement.inMeta} />
              <KeywordChip label="Intro" ok={analysis.keywordPlacement.inIntro} />
              <KeywordChip label="Headings" ok={analysis.keywordPlacement.inHeadings} />
            </div>
          </div>
          <div className="rounded-xl border border-white/[0.06] bg-surface-2 p-4">
            <p className="text-sm font-semibold text-ink">Readability Snapshot</p>
            <p className="text-xs text-ink-soft">Flesch {analysis.readability} | Grade {analysis.readingGrade}</p>
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-ink-soft">
              <span>Avg words / sentence: {analysis.sentenceAverageWords}</span>
              <span>Avg words / paragraph: {analysis.paragraphAverageWords}</span>
              <span>Structure: {analysis.headingStructureValid ? 'Valid' : 'Needs cleanup'}</span>
              <span>Suggested slug: {analysis.suggestedSlug || 'n/a'}</span>
            </div>
          </div>
        </div>

        {/* Quality Warnings from backend */}
        {draft.quality_notes && draft.quality_notes.length > 0 && (
          <div className="mt-4 rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
            <p className="text-sm font-semibold text-amber-400">Quality Warnings</p>
            <ul className="mt-2 space-y-1 text-sm text-amber-300/80">
              {draft.quality_notes.map((note) => (
                <li key={note}>- {note}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="mt-4 rounded-xl border border-white/[0.06] bg-surface-2 p-4">
          <p className="text-sm font-semibold text-ink">Recommended Before Publish</p>
          <ul className="mt-2 space-y-1 text-sm text-ink-soft">
            {analysis.suggestions.map((suggestion) => (
              <li key={suggestion}>- {suggestion}</li>
            ))}
          </ul>
        </div>
      </section>

      <section className="rounded-lg border bg-card text-card-foreground shadow-sm flex flex-wrap gap-3 p-5">
        <Button variant="secondary" onClick={handleSave} disabled={saving} type="button">
          {saving ? 'Working...' : 'Save Draft'}
        </Button>

        <Button onClick={handleApprove} disabled={saving || draft.status === 'published'} type="button">
          Approve
        </Button>

        <Button variant="destructive" onClick={handleReject} disabled={saving || draft.status === 'published'} type="button">
          Reject
        </Button>

        {draft.status === 'approved' && (
          <Button onClick={handlePublish} disabled={saving} type="button">
            Publish
          </Button>
        )}

        {draft.status === 'published' && (
          <>
            <a
              className="inline-flex h-10 items-center justify-center rounded-md border border-white/[0.10] bg-white/[0.06] px-4 py-2 text-sm font-medium text-ink transition-colors hover:bg-white/[0.10]"
              href={draft.published_url || '#'}
              target="_blank"
              rel="noreferrer"
            >
              View Published URL
            </a>
            <Button onClick={handlePublishSocial} disabled={saving} type="button">
              Publish Social Now
            </Button>
          </>
        )}
      </section>
    </main>
  );
}

function mapDraftToForm(draft: Article): DraftForm {
  return {
    content_html: sanitizeDraftHtml(draft.content_html),
    seo_title: cleanMarkdownText(draft.seo_title),
    meta_description: cleanMarkdownText(draft.meta_description),
    keywords: (draft.keywords || []).join(', '),
    issue_summary: cleanMarkdownText(draft.issue_summary),
    why_it_matters: cleanMarkdownText(draft.why_it_matters),
    mental_health_implications: cleanMarkdownText(draft.mental_health_implications),
    professional_insight: cleanMarkdownText(draft.professional_insight),
    how_services_help: cleanMarkdownText(draft.how_services_help),
    call_to_action: cleanMarkdownText(draft.call_to_action),
    social_posts: {
      instagram: cleanMarkdownText(
        draft.social_posts.find((s) => s.platform === 'instagram')?.edited_caption ||
          draft.social_posts.find((s) => s.platform === 'instagram')?.caption ||
          ''
      ),
      linkedin: cleanMarkdownText(
        draft.social_posts.find((s) => s.platform === 'linkedin')?.edited_caption ||
          draft.social_posts.find((s) => s.platform === 'linkedin')?.caption ||
          ''
      ),
      twitter: cleanMarkdownText(
        draft.social_posts.find((s) => s.platform === 'twitter')?.edited_caption ||
          draft.social_posts.find((s) => s.platform === 'twitter')?.caption ||
          ''
      ),
      facebook: cleanMarkdownText(
        draft.social_posts.find((s) => s.platform === 'facebook')?.edited_caption ||
          draft.social_posts.find((s) => s.platform === 'facebook')?.caption ||
          ''
      ),
    },
  };
}

function sanitizeDraftHtml(value: string): string {
  let html = String(value || '');

  html = html.replace(/<script[\s\S]*?<\/script>/gi, '');
  html = html.replace(/<style[\s\S]*?<\/style>/gi, '');
  html = html.replace(/Intro:\s*Summary of Issue/gi, 'Summary of Issue');

  // Remove leaked metadata/debug lines that should never be in article body.
  html = html.replace(/<p>\s*(topic:|x heading:|relevance\b|source\b|regions:|stats:)[\s\S]*?<\/p>/gi, '');

  html = html.replace(/<p>\s*(\*\*|__|---?|~~)\s*<\/p>/gi, '');

  const markers = [
    'Introduction',
    'Summary of Issue',
    "Understanding Our Children's Experiences",
    'Why This Matters',
    'Mental Health Implications',
    'Professional Insight',
    'How Horizon Therapy Centre Can Help',
    'Take the Next Step (CTA)',
  ];

  for (const marker of markers) {
    const escaped = marker.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    html = html.replace(
      new RegExp(`(<p>\\s*<strong>\\s*${escaped}\\s*<\\/strong>\\s*<\\/p>\\s*){2,}`, 'gi'),
      `<p><strong>${marker}</strong></p>`
    );
    html = html.replace(
      new RegExp(`(<p>\\s*${escaped}\\s*<\\/p>\\s*){2,}`, 'gi'),
      `<p>${marker}</p>`
    );
    html = html.replace(
      new RegExp(
        `<p>\\s*(?:<strong>\\s*)?${escaped}\\s*(?:<\\/strong>)?\\s*<\\/p>\\s*<p>\\s*(?:<strong>\\s*)?${escaped}\\s*(?:<\\/strong>)?\\s*<\\/p>`,
        'gi'
      ),
      `<p><strong>${marker}</strong></p>`
    );
  }

  const bodyHeadings = [
    'Summary of Issue',
    'Why This Matters',
    'Mental Health Implications',
    'Professional Insight',
    'How Horizon Therapy Centre Can Help',
    'Take the Next Step (CTA)',
  ];
  for (const heading of bodyHeadings) {
    const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    html = html.replace(new RegExp(`<h2[^>]*>\\s*${escaped}\\s*<\\/h2>`, 'gi'), `<h3>${heading}</h3>`);
    html = html.replace(new RegExp(`<p>\\s*<strong>\\s*${escaped}\\s*<\\/strong>\\s*<\\/p>`, 'gi'), `<h3>${heading}</h3>`);
    html = html.replace(new RegExp(`<p>\\s*${escaped}\\s*<\\/p>`, 'gi'), `<h3>${heading}</h3>`);
  }

  const footerHeadings = ['Footer Disclaimer', 'Author Info', 'Citations', 'Internal Links', 'Meta Data'];
  for (const heading of footerHeadings) {
    const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    html = html.replace(new RegExp(`<h2[^>]*>\\s*${escaped}\\s*<\\/h2>`, 'gi'), `<h3>${heading}</h3>`);
  }

  html = html.replace(/\n{3,}/g, '\n\n');
  return html.trim();
}

function cleanMarkdownText(value: string): string {
  return value
    .replace(/\r\n?/g, '\n')
    .replace(/^\s{0,3}#{1,6}\s+/gm, '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/__(.*?)__/g, '$1')
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/_(.*?)_/g, '$1')
    .replace(/`{1,3}([^`]+)`{1,3}/g, '$1')
    .replace(/\[(.*?)\]\((.*?)\)/g, '$1 ($2)')
    .replace(/^\s*[-*+]\s+/gm, '')
    .replace(/^\s*\d+\.\s+/gm, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function analyzeDraft(input: { seoTitle: string; metaDescription: string; keywords: string[]; contentHtml: string }): DraftAnalysis {
  const seoTitle = cleanMarkdownText(String(input.seoTitle || ''));
  const metaDescription = cleanMarkdownText(String(input.metaDescription || ''));
  const contentHtml = String(input.contentHtml || '');
  const plainText = stripHtmlToText(contentHtml);
  const words = extractWords(plainText);
  const sentences = splitSentences(plainText);
  const paragraphs = extractParagraphTexts(contentHtml);
  const headings = extractHeadings(contentHtml);
  const headingCounts = {
    h1: headings.filter((item) => item.level === 1).length,
    h2: headings.filter((item) => item.level === 2).length,
    h3: headings.filter((item) => item.level === 3).length,
  };
  const hasSkippedHeadingLevels = headings.some((item, index) => index > 0 && item.level > headings[index - 1].level + 1);

  const headingIssues: string[] = [];
  if (!headings.length) {
    headingIssues.push('Add clear section headings in the article body.');
  }
  if (headingCounts.h1 === 0) {
    headingIssues.push('Add one H1 in the article body.');
  }
  if (headingCounts.h1 > 1) {
    headingIssues.push('Use a single H1 to avoid structure conflicts.');
  }
  if (headingCounts.h2 === 0 && headingCounts.h3 > 0) {
    headingIssues.push('Add H2 sections before using H3 subsections.');
  }
  if (hasSkippedHeadingLevels) {
    headingIssues.push('Avoid skipping heading levels (for example H1 to H3).');
  }

  const wordCount = words.length;
  const readingTimeMinutes = Math.max(1, Math.ceil(wordCount / 220));
  const sentenceAverageWords = roundToOne(wordCount / Math.max(sentences.length, 1));
  const paragraphWordCount = paragraphs.reduce((sum, paragraph) => sum + extractWords(paragraph).length, 0);
  const paragraphAverageWords = roundToOne(paragraphWordCount / Math.max(paragraphs.length, 1));

  const syllables = words.reduce((sum, word) => sum + countSyllables(word), 0);
  const readabilityRaw = wordCount > 0 && sentences.length > 0 ? 206.835 - 1.015 * (wordCount / sentences.length) - 84.6 * (syllables / wordCount) : 0;
  const readingGradeRaw = wordCount > 0 && sentences.length > 0 ? 0.39 * (wordCount / sentences.length) + 11.8 * (syllables / wordCount) - 15.59 : 0;
  const readability = roundToOne(clamp(readabilityRaw, 0, 120));
  const readingGrade = roundToOne(clamp(readingGradeRaw, 0, 20));

  const primaryKeyword = input.keywords[0]?.trim() || null;
  const keywordNeedle = primaryKeyword ? primaryKeyword.toLowerCase() : null;
  const introText = words.slice(0, 120).join(' ').toLowerCase();
  const headingText = headings.map((item) => item.text.toLowerCase()).join(' ');
  const keywordPlacement = {
    inTitle: Boolean(keywordNeedle && seoTitle.toLowerCase().includes(keywordNeedle)),
    inMeta: Boolean(keywordNeedle && metaDescription.toLowerCase().includes(keywordNeedle)),
    inIntro: Boolean(keywordNeedle && introText.includes(keywordNeedle)),
    inHeadings: Boolean(keywordNeedle && headingText.includes(keywordNeedle)),
  };
  const keywordHits = Object.values(keywordPlacement).filter(Boolean).length;

  const siteHostname = typeof window !== 'undefined' ? window.location.hostname : '';
  const links = collectLinkStats(contentHtml, siteHostname);
  const images = collectImageStats(contentHtml);
  const suggestedSlug = createSlug(seoTitle);
  const slugLength = suggestedSlug.length;
  const titleLength = seoTitle.length;
  const metaLength = metaDescription.length;

  const titleScore = scoreByLength(titleLength, 45, 65, 15);
  const metaScore = scoreByLength(metaLength, 120, 160, 25);
  const slugScore = scoreByLength(slugLength, 20, 75, 20);
  const keywordScore = primaryKeyword ? Math.round((keywordHits / 4) * 100) : 20;
  let headingScore = 100;
  if (!headings.length) headingScore -= 55;
  if (headingCounts.h1 === 0) headingScore -= 15;
  if (headingCounts.h1 > 1) headingScore -= 35;
  if (headingCounts.h2 === 0 && headingCounts.h3 > 0) headingScore -= 15;
  if (hasSkippedHeadingLevels) headingScore -= 20;
  headingScore = clamp(headingScore, 0, 100);
  const wordScore =
    wordCount >= 900 && wordCount <= 1100 ? 100 : wordCount >= 750 && wordCount <= 1300 ? 70 : wordCount >= 200 ? 45 : wordCount > 0 ? 25 : 0;
  const linkScore =
    links.invalid > 0 ? (links.internal + links.external > 0 ? 45 : 20) : links.internal >= 1 && links.external >= 1 ? 100 : links.internal + links.external > 0 ? 70 : 30;
  const imageScore = images.total > 0 ? images.altCoverage : 75;
  const readabilityScore =
    readability >= 45 && readability <= 75 ? 100 : readability >= 35 && readability < 45 ? 70 : readability > 75 && readability <= 85 ? 70 : readability > 0 ? 45 : 30;

  const weightedScore =
    titleScore * 0.11
    + metaScore * 0.11
    + slugScore * 0.08
    + keywordScore * 0.18
    + headingScore * 0.16
    + wordScore * 0.11
    + linkScore * 0.1
    + imageScore * 0.07
    + readabilityScore * 0.08;
  const score = Math.round(clamp(weightedScore, 0, 100));

  const suggestions: string[] = [];
  if (titleScore < 100) {
    suggestions.push('Keep SEO title around 45-65 characters.');
  }
  if (metaScore < 100) {
    suggestions.push('Keep meta description around 120-160 characters.');
  }
  if (slugScore < 70) {
    suggestions.push('Use a short, readable slug with key terms from the title.');
  }
  if (!primaryKeyword) {
    suggestions.push('Set your primary keyword as the first keyword in the list.');
  } else if (keywordHits < 3) {
    suggestions.push(`Place "${primaryKeyword}" in title, intro, and at least one heading.`);
  }
  suggestions.push(...headingIssues);
  if (wordScore < 100) {
    suggestions.push('Target 900-1100 words (~1000) for optimal readability and SEO coverage.');
  }
  if (links.internal === 0) {
    suggestions.push('Add at least one internal link to a related page or service.');
  }
  if (links.external === 0) {
    suggestions.push('Add at least one trusted external reference link.');
  }
  if (links.invalid > 0) {
    suggestions.push('Fix invalid URLs before publishing.');
  }
  if (images.total > 0 && images.altCoverage < 100) {
    suggestions.push('Add alt text to all images for accessibility and SEO.');
  }
  if (readabilityScore < 70) {
    suggestions.push('Shorten long sentences to improve readability.');
  }

  const uniqueSuggestions = Array.from(new Set(suggestions)).slice(0, 8);
  if (!uniqueSuggestions.length) {
    uniqueSuggestions.push('No major issues found. Draft looks ready for editorial decision.');
  }

  return {
    score,
    titleLength,
    metaLength,
    slugLength,
    suggestedSlug,
    wordCount,
    readingTimeMinutes,
    sentenceAverageWords,
    paragraphAverageWords,
    readability,
    readingGrade,
    primaryKeyword,
    keywordPlacement,
    headingCounts,
    headingStructureValid: headingIssues.length === 0,
    headingIssues,
    links,
    images,
    titleScore,
    metaScore,
    slugScore,
    keywordScore,
    headingScore,
    wordScore,
    linkScore,
    imageScore,
    readabilityScore,
    suggestions: uniqueSuggestions,
  };
}

function scoreByLength(length: number, idealMin: number, idealMax: number, softBuffer: number): number {
  if (length >= idealMin && length <= idealMax) {
    return 100;
  }
  if (length >= idealMin - softBuffer && length <= idealMax + softBuffer) {
    return 70;
  }
  if (length > 0) {
    return 40;
  }
  return 0;
}

function collectLinkStats(contentHtml: string, siteHostname?: string): { internal: number; external: number; invalid: number } {
  let internal = 0;
  let external = 0;
  let invalid = 0;
  const matches = Array.from(contentHtml.matchAll(/<a\b[^>]*href=["']([^"']+)["'][^>]*>/gi));
  for (const match of matches) {
    const href = String(match[1] || '').trim();
    if (!href) {
      continue;
    }
    if (href.startsWith('/') || href.startsWith('#')) {
      internal += 1;
      continue;
    }
    if (/^https?:\/\//i.test(href)) {
      try {
        const url = new URL(href);
        // Treat same-domain absolute URLs as internal links
        if (siteHostname && url.hostname === siteHostname) {
          internal += 1;
        } else {
          external += 1;
        }
      } catch {
        invalid += 1;
      }
      continue;
    }
    if (/^(mailto|tel):/i.test(href)) {
      continue;
    }
    if (!/^[a-z]+:/i.test(href) && !href.startsWith('//')) {
      internal += 1;
      continue;
    }
    invalid += 1;
  }
  return { internal, external, invalid };
}

function collectImageStats(contentHtml: string): { total: number; withAlt: number; altCoverage: number } {
  const images = contentHtml.match(/<img\b[^>]*>/gi) || [];
  const withAlt = images.reduce((sum, imageTag) => {
    const alt = imageTag.match(/\balt\s*=\s*(['"])(.*?)\1/i);
    return alt && String(alt[2] || '').trim() ? sum + 1 : sum;
  }, 0);
  const altCoverage = images.length > 0 ? Math.round((withAlt / images.length) * 100) : 100;
  return {
    total: images.length,
    withAlt,
    altCoverage,
  };
}

function createSlug(value: string): string {
  return value
    .toLowerCase()
    .replace(/&/g, ' and ')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .replace(/-{2,}/g, '-')
    .slice(0, 90);
}

function extractHeadings(contentHtml: string): Array<{ level: number; text: string }> {
  const headings: Array<{ level: number; text: string }> = [];
  const regex = /<h([1-6])\b[^>]*>([\s\S]*?)<\/h\1>/gi;
  let match: RegExpExecArray | null = regex.exec(contentHtml);
  while (match) {
    const level = Number(match[1] || 0);
    const text = stripHtmlToText(match[2] || '').trim();
    if (level >= 1 && level <= 6 && text) {
      headings.push({ level, text });
    }
    match = regex.exec(contentHtml);
  }
  return headings;
}

function extractParagraphTexts(contentHtml: string): string[] {
  return contentHtml
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<\/(p|li|div|h[1-6]|section|article|blockquote)>/gi, '\n')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<[^>]+>/g, ' ')
    .split(/\n+/)
    .map((line) => decodeHtmlEntities(line).replace(/\s+/g, ' ').trim())
    .filter(Boolean);
}

function stripHtmlToText(value: string): string {
  return decodeHtmlEntities(
    value
      .replace(/<script[\s\S]*?<\/script>/gi, ' ')
      .replace(/<style[\s\S]*?<\/style>/gi, ' ')
      .replace(/<br\s*\/?>/gi, ' ')
      .replace(/<[^>]+>/g, ' ')
      .replace(/\s+/g, ' ')
  ).trim();
}

function decodeHtmlEntities(value: string): string {
  return value
    .replace(/&nbsp;/gi, ' ')
    .replace(/&amp;/gi, '&')
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>')
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/g, "'");
}

function extractWords(value: string): string[] {
  return value.toLowerCase().match(/[a-z0-9']+/g) || [];
}

function splitSentences(value: string): string[] {
  return value
    .split(/[.!?]+/)
    .map((line) => line.trim())
    .filter((line) => extractWords(line).length > 0);
}

function countSyllables(word: string): number {
  const cleaned = word.toLowerCase().replace(/[^a-z]/g, '');
  if (!cleaned) {
    return 0;
  }
  if (cleaned.length <= 3) {
    return 1;
  }

  const withoutSilentE = cleaned.replace(/e$/, '');
  const groups = withoutSilentE.match(/[aeiouy]{1,2}/g);
  return Math.max(1, groups ? groups.length : 1);
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function roundToOne(value: number): number {
  return Math.round(value * 10) / 10;
}

function toneFromScore(score: number): HealthTone {
  if (score >= 80) {
    return 'good';
  }
  if (score >= 60) {
    return 'warn';
  }
  return 'bad';
}

function toneClasses(tone: HealthTone): string {
  if (tone === 'good') {
    return 'border-emerald-500/20 bg-emerald-500/10 text-emerald-400';
  }
  if (tone === 'warn') {
    return 'border-apple-blue/20 bg-apple-blue/10 text-apple-blue';
  }
  return 'border-red-500/20 bg-red-500/10 text-red-400';
}

function ScorePill({ score }: { score: number }) {
  const tone = toneFromScore(score);
  return (
    <div className={`rounded-xl border px-3 py-2 text-sm font-semibold ${toneClasses(tone)}`}>
      SEO Score {score}/100
    </div>
  );
}

function AnalyzerMetric({ label, value, hint, tone }: { label: string; value: string; hint: string; tone: HealthTone }) {
  return (
    <div className={`rounded-xl border p-3 ${toneClasses(tone)}`}>
      <p className="text-xs font-semibold uppercase tracking-[0.08em]">{label}</p>
      <p className="mt-1 text-sm font-semibold">{value}</p>
      <p className="mt-1 text-xs">{hint}</p>
    </div>
  );
}

function KeywordChip({ label, ok }: { label: string; ok: boolean }) {
  return (
    <span
      className={`rounded-lg border px-2.5 py-1 text-xs font-medium ${
        ok ? 'border-emerald-500/20 bg-emerald-500/10 text-emerald-400' : 'border-white/[0.06] bg-surface-3 text-ink-soft'
      }`}
    >
      {label}: {ok ? 'Yes' : 'No'}
    </span>
  );
}

function PublishReadinessBadge({ draft }: { draft: Article }) {
  const hasQualityIssues = draft.requires_review === true;
  const hasHighAi = (draft.ai_generated_probability ?? 0) > 0.6;
  const hasHighPlagiarism = (draft.source_similarity_score ?? 0) > 0.16;
  const needsAttention = hasQualityIssues || hasHighAi || hasHighPlagiarism || !draft.structure_valid;

  if (needsAttention) {
    return (
      <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 px-3 py-2 text-sm font-semibold text-amber-400">
        Needs Review
      </div>
    );
  }
  return (
    <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-3 py-2 text-sm font-semibold text-emerald-400">
      Ready to Publish
    </div>
  );
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-ink-soft">{label}</label>
      <Input value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

function TextAreaField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium capitalize text-ink-soft">{label}</label>
      <Textarea className="min-h-32" value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}
