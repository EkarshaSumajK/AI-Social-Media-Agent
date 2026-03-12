'use client';

import { useMemo, useState } from 'react';
import { Check, Copy, ImageIcon, Loader2, Send, X } from 'lucide-react';

import { ImageGeneratorModal } from '@/components/image-generator/ImageGeneratorModal';
import type { Platform } from '@/components/image-generator/types';
import { PageHeader } from '@/components/page-header';

const FORMAT_TO_PLATFORM: Record<string, Platform> = {
  linkedin_post: 'linkedin',
  thread:        'twitter',
  tweet:         'twitter',
  reel_script:   'instagram',
  quote_card:    'threads',
  blog_summary:  'linkedin',
  email_series:  'linkedin',
};
import { Button } from '@/components/ui/button';
import { AppSelect } from '@/components/ui/app-select';
import { Textarea } from '@/components/ui/textarea';
import { repurposeContent, publishToSocial } from '@/lib/api';
import { REPURPOSE_TARGET_FORMATS } from '@/lib/types';
import type { RepurposeResponse, RepurposeSourceType } from '@/lib/types';

const SOURCE_TYPES: { value: RepurposeSourceType; label: string }[] = [
  { value: 'article', label: 'Article' },
  { value: 'blog', label: 'Blog' },
  { value: 'webinar', label: 'Webinar' },
];

const FORMAT_LABELS: Record<string, string> = {
  linkedin_post: 'LinkedIn Post',
  thread: 'Thread',
  reel_script: 'Reel Script',
  tweet: 'Tweet',
  blog_summary: 'Blog Summary',
  quote_card: 'Quote Card',
  email_series: 'Email Series',
};

const SOCIAL_PLATFORM_OPTIONS = [
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'twitter', label: 'X / Twitter' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'facebook', label: 'Facebook' },
];

function ApprovePublishInline({ content, defaultPlatform }: { content: string; defaultPlatform?: string }) {
  const [open, setOpen] = useState(false);
  const [platform, setPlatform] = useState(defaultPlatform ?? 'linkedin');
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

export default function RepurposePage() {
  const [content, setContent] = useState('');
  const [sourceType, setSourceType] = useState<RepurposeSourceType>('article');
  const [targetFormats, setTargetFormats] = useState<string[]>(['linkedin_post', 'twitter_thread']);
  const [result, setResult] = useState<RepurposeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [imageModal, setImageModal] = useState<{ open: boolean; content: string; platform: Platform } | null>(null);

  const outputEntries = useMemo(() => {
    if (!result) {
      return [];
    }
    const flattened: Array<{ format: string; content: string; index: number }> = [];
    for (const [format, pieces] of Object.entries(result.results || {})) {
      const rows = Array.isArray(pieces) ? pieces : [String(pieces)];
      rows.forEach((piece, index) => {
        flattened.push({ format, content: String(piece), index });
      });
    }
    return flattened;
  }, [result]);

  function toggleFormat(format: string) {
    setTargetFormats((previous) =>
      previous.includes(format)
        ? previous.filter((item) => item !== format)
        : [...previous, format]
    );
  }

  async function handleGenerate() {
    const trimmed = content.trim();
    if (!trimmed) {
      setError('Please enter source content.');
      return;
    }
    if (targetFormats.length === 0) {
      setError('Please select at least one target format.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await repurposeContent({
        content: trimmed,
        source_type: sourceType,
        target_formats: targetFormats,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to repurpose content');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-6 p-4 sm:p-6">
      <PageHeader
        title="Repurpose Content"
        description="Transform a source asset into backend-supported output formats"
      />

      <section className="rounded-lg border bg-card p-5 text-card-foreground shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-ink">Source content</h2>

        <div className="grid gap-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-ink">Paste your content</label>
            <Textarea
              className="min-h-[180px] resize-y"
              value={content}
              onChange={(event) => setContent(event.target.value)}
              placeholder="Paste article/blog/webinar notes to repurpose..."
              disabled={loading}
            />
          </div>

          <div className="max-w-xs">
            <label className="mb-1.5 block text-sm font-medium text-ink">Source type</label>
            <AppSelect
              value={sourceType}
              onValueChange={(value) => setSourceType(value as RepurposeSourceType)}
              disabled={loading}
              options={SOURCE_TYPES.map((item) => ({ value: item.value, label: item.label }))}
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-ink">Target formats</label>
            <div className="flex flex-wrap gap-3">
              {REPURPOSE_TARGET_FORMATS.map((format) => (
                <label
                  key={format.value}
                  className="flex cursor-pointer items-center gap-2 rounded-lg border border-white/[0.06] bg-surface-2 px-3 py-2 text-sm transition hover:border-apple-blue/30"
                >
                  <input
                    type="checkbox"
                    checked={targetFormats.includes(format.value)}
                    onChange={() => toggleFormat(format.value)}
                    disabled={loading}
                    className="h-4 w-4 rounded border-white/[0.08] bg-transparent text-apple-blue"
                  />
                  <span className="text-ink">{format.label}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        <Button className="mt-4 w-full sm:w-fit" onClick={handleGenerate} disabled={loading}>
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Repurposing...
            </>
          ) : (
            'Generate Repurposed Outputs'
          )}
        </Button>
      </section>

      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {outputEntries.length > 0 && (
        <section className="rounded-lg border bg-card p-5 text-card-foreground shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-ink">Output formats</h2>
          <div className="grid gap-4 md:grid-cols-2">
            {outputEntries.map((output) => (
              <article
                key={`${output.format}-${output.index}`}
                className="rounded-xl border border-white/[0.06] bg-surface-2 p-4"
              >
                <div className="mb-3 flex items-center justify-between gap-2">
                  <span className="inline-flex rounded-full bg-moss/20 px-2.5 py-0.5 text-xs font-semibold text-moss">
                    {FORMAT_LABELS[output.format] || output.format}
                  </span>
                  <div className="flex flex-wrap items-center gap-1.5">
                    <ApprovePublishInline
                      content={output.content}
                      defaultPlatform={FORMAT_TO_PLATFORM[output.format] ?? 'linkedin'}
                    />
                    <button
                      type="button"
                      onClick={() => setImageModal({ open: true, content: output.content, platform: FORMAT_TO_PLATFORM[output.format] ?? 'linkedin' })}
                      className="flex h-7 items-center gap-1 rounded-md border border-white/[0.06] bg-white/[0.03] px-2 text-[11px] text-ink-faint transition hover:border-apple-blue/30 hover:bg-apple-blue/10 hover:text-apple-blue"
                    >
                      <ImageIcon size={11} /> Image
                    </button>
                    <CopyButton text={output.content} />
                  </div>
                </div>
                <div className="whitespace-pre-wrap text-sm text-ink">{output.content}</div>
              </article>
            ))}
          </div>
        </section>
      )}

      {result && outputEntries.length === 0 && !loading && (
        <p className="text-sm text-ink-soft">No outputs returned. Try different formats.</p>
      )}

      {imageModal && (
        <ImageGeneratorModal
          open={imageModal.open}
          onOpenChange={(open) => setImageModal((s) => s ? { ...s, open } : null)}
          content={imageModal.content}
          platform={imageModal.platform}
        />
      )}
    </div>
  );
}
