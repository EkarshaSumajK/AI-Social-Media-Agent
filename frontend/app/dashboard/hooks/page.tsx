'use client';

import { Loader2 } from 'lucide-react';
import { useEffect, useState } from 'react';

import { ListCard } from '@/components/list-card';
import { PageHeader } from '@/components/page-header';
import { PageShell } from '@/components/page-shell';
import { AppSelect } from '@/components/ui/app-select';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { createHook, fetchHooks, suggestHooks } from '@/lib/api';
import type { HookSuggestionResponse, HookTemplate } from '@/lib/types';
import { SOCIAL_PLATFORMS } from '@/lib/types';

const HOOK_CATEGORIES = [
  'question',
  'statistic',
  'story',
  'contrarian',
  'how_to',
  'list',
  'fear',
  'curiosity',
  'authority',
  'other',
];

type TabId = 'browse' | 'create' | 'suggest';

function labelize(value: string) {
  return value
    .split('_')
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(' ');
}

export default function HooksPage() {
  const [activeTab, setActiveTab] = useState<TabId>('browse');
  const [hooks, setHooks] = useState<HookTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [categoryFilter, setCategoryFilter] = useState<string>('');

  const [createCategory, setCreateCategory] = useState('question');
  const [createHookText, setCreateHookText] = useState('');
  const [createPlatform, setCreatePlatform] = useState('linkedin');
  const [createSubmitting, setCreateSubmitting] = useState(false);

  const [suggestTopic, setSuggestTopic] = useState('');
  const [suggestPlatform, setSuggestPlatform] = useState('linkedin');
  const [suggestSubmitting, setSuggestSubmitting] = useState(false);
  const [suggestedHooks, setSuggestedHooks] = useState<HookSuggestionResponse | null>(null);

  async function loadHooks() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchHooks(categoryFilter || undefined);
      setHooks(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load hooks');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (activeTab === 'browse') {
      void loadHooks();
    }
  }, [activeTab, categoryFilter]);

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    const trimmedHookText = createHookText.trim();

    if (!trimmedHookText) {
      setError('Hook text is required.');
      return;
    }

    setCreateSubmitting(true);
    setError(null);

    try {
      await createHook({
        category: createCategory,
        hook_text: trimmedHookText,
        platform: createPlatform,
      });
      setCreateHookText('');
      if (activeTab === 'browse') {
        await loadHooks();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create hook');
    } finally {
      setCreateSubmitting(false);
    }
  }

  async function handleSuggest(event: React.FormEvent) {
    event.preventDefault();
    const trimmedTopic = suggestTopic.trim();

    if (!trimmedTopic) {
      setError('Topic is required.');
      return;
    }

    setSuggestSubmitting(true);
    setError(null);
    setSuggestedHooks(null);

    try {
      const result = await suggestHooks(trimmedTopic, suggestPlatform, 5);
      setSuggestedHooks(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to suggest hooks');
    } finally {
      setSuggestSubmitting(false);
    }
  }

  const tabs: { id: TabId; label: string }[] = [
    { id: 'browse', label: 'Browse' },
    { id: 'create', label: 'Create' },
    { id: 'suggest', label: 'Suggest' },
  ];

  return (
    <PageShell>
      <PageHeader title="Viral Hook Library" description="Browse, create, and get AI-suggested hooks" />

      {error && (
        <div className="rounded-xl border border-ember/30 bg-ember/5 px-4 py-3 text-sm text-ember">
          {error}
        </div>
      )}

      <div className="flex gap-2 border-b border-white/[0.06]">
        {tabs.map((tab) => (
          <Button
            key={tab.id}
            type="button"
            variant="ghost"
            onClick={() => setActiveTab(tab.id)}
            className={`border-b-2 px-4 py-2 text-sm font-medium transition ${
              activeTab === tab.id
                ? 'border-apple-blue text-apple-blue'
                : 'border-transparent text-ink-soft hover:text-ink'
            }`}
          >
            {tab.label}
          </Button>
        ))}
      </div>

      {activeTab === 'browse' && (
        <section className="flex flex-col gap-6">
          <div className="flex flex-wrap items-center gap-3">
            <label className="text-sm font-medium text-ink">Category</label>
            <AppSelect
              value={categoryFilter}
              onValueChange={setCategoryFilter}
              triggerClassName="w-48"
              options={[
                { value: '', label: 'All' },
                ...HOOK_CATEGORIES.map((value) => ({ value, label: labelize(value) })),
              ]}
            />
          </div>

          {loading ? (
            <div className="flex items-center gap-2 py-12 text-sm text-ink-soft">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading hooks...
            </div>
          ) : hooks.length === 0 ? (
            <div className="flex flex-col items-center gap-4 rounded-lg border border-dashed border-white/[0.08] bg-white/[0.02] py-16">
              <p className="text-sm text-ink-soft">No hooks found.</p>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {hooks.map((hook) => (
                <ListCard
                  key={hook.id}
                  title={hook.hook_text}
                  metadata={
                    <>
                      <span>{labelize(hook.platform)}</span>
                      <span>•</span>
                      <span>Used {hook.use_count}x</span>
                    </>
                  }
                  tags={
                    <span className="rounded-md border border-apple-blue/20 bg-apple-blue/10 px-2 py-0.5 text-xs font-medium text-apple-blue">
                      {labelize(hook.category)}
                    </span>
                  }
                  actions={[{ label: 'View details', href: `/dashboard/hooks/${hook.id}` }]}
                  href={`/dashboard/hooks/${hook.id}`}
                />
              ))}
            </div>
          )}
        </section>
      )}

      {activeTab === 'create' && (
        <section className="max-w-xl rounded-lg border bg-card p-5 text-card-foreground shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-ink">Create Hook</h2>
          <form onSubmit={handleCreate} className="flex flex-col gap-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink">Category</label>
              <AppSelect
                value={createCategory}
                onValueChange={setCreateCategory}
                disabled={createSubmitting}
                options={HOOK_CATEGORIES.map((value) => ({ value, label: labelize(value) }))}
              />
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink">Hook text</label>
              <Textarea
                className="min-h-[100px] resize-y"
                value={createHookText}
                onChange={(event) => setCreateHookText(event.target.value)}
                placeholder="Enter your hook..."
                disabled={createSubmitting}
              />
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink">Platform</label>
              <AppSelect
                value={createPlatform}
                onValueChange={setCreatePlatform}
                disabled={createSubmitting}
                options={SOCIAL_PLATFORMS.map((value) => ({ value, label: labelize(value) }))}
              />
            </div>

            <Button type="submit" className="w-full sm:w-fit" disabled={createSubmitting}>
              {createSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create Hook'
              )}
            </Button>
          </form>
        </section>
      )}

      {activeTab === 'suggest' && (
        <section className="max-w-xl rounded-lg border bg-card p-5 text-card-foreground shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-ink">AI-Suggested Hooks</h2>
          <form onSubmit={handleSuggest} className="mb-6 flex flex-col gap-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink">Topic</label>
              <Input
                value={suggestTopic}
                onChange={(event) => setSuggestTopic(event.target.value)}
                placeholder="e.g. productivity, mental health"
                disabled={suggestSubmitting}
              />
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink">Platform</label>
              <AppSelect
                value={suggestPlatform}
                onValueChange={setSuggestPlatform}
                disabled={suggestSubmitting}
                options={SOCIAL_PLATFORMS.map((value) => ({ value, label: labelize(value) }))}
              />
            </div>

            <Button type="submit" className="w-full sm:w-fit" disabled={suggestSubmitting}>
              {suggestSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Suggesting...
                </>
              ) : (
                'Suggest Hooks'
              )}
            </Button>
          </form>

          {suggestedHooks && (
            <div className="rounded-xl border border-white/[0.06] bg-surface-2 p-4">
              <ul className="space-y-3">
                {suggestedHooks.suggestions.map((item, index) => (
                  <li key={`${item.hook_text}-${index}`} className="rounded-lg border border-white/[0.06] bg-surface-3 p-3">
                    <p className="text-sm font-medium text-ink">{item.hook_text}</p>
                    {item.reasoning && (
                      <p className="mt-1 text-xs text-ink-soft">{item.reasoning}</p>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}
    </PageShell>
  );
}
