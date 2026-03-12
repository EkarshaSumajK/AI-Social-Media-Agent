'use client';

import { Copy, Loader2 } from 'lucide-react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { AppSelect } from '@/components/ui/app-select';
import { useState } from 'react';

import { PageHeader } from '@/components/page-header';
import { paraphraseContent } from '@/lib/api';

const STYLES = [
  { value: 'professional', label: 'Professional' },
  { value: 'casual', label: 'Casual' },
  { value: 'academic', label: 'Academic' },
  { value: 'creative', label: 'Creative' },
  { value: 'simplified', label: 'Simplified' },
];

const TONES = [
  { value: 'supportive and clear', label: 'Supportive and clear' },
  { value: 'authoritative', label: 'Authoritative' },
  { value: 'conversational', label: 'Conversational' },
  { value: 'empathetic', label: 'Empathetic' },
  { value: 'motivational', label: 'Motivational' },
];

export default function ParaphraserPage() {
  const [content, setContent] = useState('');
  const [style, setStyle] = useState('professional');
  const [tone, setTone] = useState('supportive and clear');
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function handleParaphrase() {
    const trimmed = content.trim();
    if (!trimmed) {
      setError('Please enter content to paraphrase');
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await paraphraseContent(trimmed, style, tone);
      setResult(res.paraphrased);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to paraphrase');
    } finally {
      setLoading(false);
    }
  }

  async function handleCopy() {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError('Failed to copy to clipboard');
    }
  }

  return (
    <div className="flex flex-col gap-6 p-4 sm:p-6">
      <PageHeader
        title="Content Paraphraser"
        description="Rephrase and refine your content with AI"
      />

      {error && (
        <div className="rounded-xl border border-ember/30 bg-ember/5 px-4 py-3 text-sm text-ember">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-lg border bg-card text-card-foreground shadow-sm flex flex-col p-5">
          <h2 className="mb-4 text-lg font-semibold text-ink">Input</h2>
          <div className="mb-4 flex flex-col gap-4 sm:flex-row">
            <div className="flex-1">
              <label className="mb-1.5 block text-sm font-medium text-ink">Style</label>
              <AppSelect
                value={style}
                onValueChange={setStyle}
                disabled={loading}
                options={STYLES}
              />
            </div>
            <div className="flex-1">
              <label className="mb-1.5 block text-sm font-medium text-ink">Tone</label>
              <AppSelect
                value={tone}
                onValueChange={setTone}
                disabled={loading}
                options={TONES}
              />
            </div>
          </div>
          <label className="mb-1.5 block text-sm font-medium text-ink">Content</label>
          <Textarea
            className="min-h-[280px] flex-1 resize-y"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Paste or type content to paraphrase..."
            disabled={loading}
          />
          <Button
            type="button"
            className="mt-4 w-fit"
            onClick={handleParaphrase}
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Paraphrasing...
              </>
            ) : (
              'Paraphrase'
            )}
          </Button>
        </section>

        <section className="rounded-lg border bg-card text-card-foreground shadow-sm flex flex-col p-5">
          <h2 className="mb-4 text-lg font-semibold text-ink">Output</h2>
          <div className="relative min-h-[280px] flex-1 rounded-xl border border-white/[0.06] bg-surface-2 p-4">
            {result ? (
              <>
                <p className="whitespace-pre-wrap text-sm text-ink">{result}</p>
                <Button
                  type="button"
                  variant="secondary" className="absolute right-4 top-4 flex items-center gap-1.5"
                  onClick={handleCopy}
                >
                  {copied ? (
                    'Copied!'
                  ) : (
                    <>
                      <Copy className="h-4 w-4" />
                      Copy
                    </>
                  )}
                </Button>
              </>
            ) : (
              <p className="text-sm text-ink-soft">
                Paraphrased content will appear here after you click Paraphrase.
              </p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
