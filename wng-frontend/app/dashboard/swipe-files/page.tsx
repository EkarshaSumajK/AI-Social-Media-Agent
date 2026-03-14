'use client';

import { Loader2, Plus, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';

import { ListCard } from '@/components/list-card';
import { PageHeader } from '@/components/page-header';
import { PageShell } from '@/components/page-shell';
import { AppSelect } from '@/components/ui/app-select';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { createSwipeFile, deleteSwipeFile, fetchSwipeFiles } from '@/lib/api';
import type { SwipeFile } from '@/lib/types';
import { PLATFORMS } from '@/lib/types';

export default function SwipeFilesPage() {
  const [swipeFiles, setSwipeFiles] = useState<SwipeFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [platform, setPlatform] = useState('horizon');
  const [tagsInput, setTagsInput] = useState('');
  const [performanceNotes, setPerformanceNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
  const [addOpen, setAddOpen] = useState(false);

  async function loadSwipeFiles() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchSwipeFiles();
      setSwipeFiles(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load swipe files');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSwipeFiles();
  }, []);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    const trimmedTitle = title.trim();
    const trimmedContent = content.trim();
    if (!trimmedTitle || !trimmedContent) {
      setError('Title and content are required');
      return;
    }
    const tags = tagsInput
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);
    setSubmitting(true);
    setError(null);
    try {
      await createSwipeFile({
        title: trimmedTitle,
        content: trimmedContent,
        source_url: sourceUrl.trim() || undefined,
        platform,
        tags: tags.length ? tags : undefined,
        performance_notes: performanceNotes.trim() || undefined,
      });
      setTitle('');
      setContent('');
      setSourceUrl('');
      setTagsInput('');
      setPerformanceNotes('');
      setAddOpen(false);
      await loadSwipeFiles();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add swipe file');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: number) {
    if (confirmDeleteId !== id) {
      setConfirmDeleteId(id);
      return;
    }
    setDeletingId(id);
    setError(null);
    try {
      await deleteSwipeFile(id);
      setConfirmDeleteId(null);
      await loadSwipeFiles();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete swipe file');
    } finally {
      setDeletingId(null);
    }
  }

  function truncate(str: string, len: number) {
    if (str.length <= len) return str;
    return str.slice(0, len) + '...';
  }

  return (
    <PageShell>
      <PageHeader
        title="Swipe Files"
        description="Save and organize high-performing content for inspiration"
      >
        <Dialog open={addOpen} onOpenChange={setAddOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Add Swipe File
            </Button>
          </DialogTrigger>
          <DialogContent className="max-h-[90vh] overflow-y-auto border-white/[0.06] bg-card sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>Add Swipe File</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleAdd} className="flex flex-col gap-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-ink">Title</label>
                <Input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Viral post about productivity"
                  disabled={submitting}
                  className="border-white/[0.08] bg-white/[0.03]"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-ink">Content</label>
                <Textarea
                  className="min-h-[120px] resize-y border-white/[0.08] bg-white/[0.03]"
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Paste the content..."
                  disabled={submitting}
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-ink">Source URL</label>
                <Input
                  type="url"
                  value={sourceUrl}
                  onChange={(e) => setSourceUrl(e.target.value)}
                  placeholder="https://..."
                  disabled={submitting}
                  className="border-white/[0.08] bg-white/[0.03]"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-ink">Platform</label>
                <AppSelect
                  value={platform}
                  onValueChange={setPlatform}
                  disabled={submitting}
                  options={PLATFORMS.map((item) => ({ value: item.value, label: item.label }))}
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-ink">Tags (comma-separated)</label>
                <Input
                  value={tagsInput}
                  onChange={(e) => setTagsInput(e.target.value)}
                  placeholder="e.g. productivity, viral, linkedin"
                  disabled={submitting}
                  className="border-white/[0.08] bg-white/[0.03]"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-ink">Performance notes</label>
                <Textarea
                  className="min-h-[80px] resize-y border-white/[0.08] bg-white/[0.03]"
                  value={performanceNotes}
                  onChange={(e) => setPerformanceNotes(e.target.value)}
                  placeholder="Optional performance observations"
                  disabled={submitting}
                />
              </div>
              <Button type="submit" disabled={submitting}>
                {submitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Adding...
                  </>
                ) : (
                  'Add Swipe File'
                )}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </PageHeader>

      <div className="flex flex-col gap-6">
        {error && (
          <div className="rounded-lg border border-ember/30 bg-ember/5 px-4 py-3 text-sm text-ember">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center gap-2 py-12 text-sm text-ink-soft">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading swipe files...
          </div>
        ) : swipeFiles.length === 0 ? (
          <div className="flex flex-col items-center gap-4 rounded-lg border border-dashed border-white/[0.08] bg-white/[0.02] py-16">
            <p className="text-sm text-ink-soft">No swipe files yet. Add one to get started.</p>
            <Button onClick={() => setAddOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Add Swipe File
            </Button>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {swipeFiles.map((sf) => (
              <ListCard
                key={sf.id}
                title={sf.title}
                metadata={
                  <>
                    <span>{sf.platform}</span>
                    {sf.source_url && (
                      <>
                        <span>•</span>
                        <a
                          href={sf.source_url}
                          target="_blank"
                          rel="noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="truncate max-w-[180px] inline-block text-apple-blue/80 hover:text-apple-blue hover:underline"
                        >
                          Source
                        </a>
                      </>
                    )}
                  </>
                }
                tags={
                  <>
                    <span className="rounded-md border border-apple-blue/20 bg-apple-blue/10 px-2 py-0.5 text-xs font-medium text-apple-blue">
                      {sf.platform}
                    </span>
                    {sf.tags?.map((tag) => (
                      <span
                        key={tag}
                        className="rounded-md border border-white/[0.06] bg-white/[0.04] px-2 py-0.5 text-xs text-ink-soft"
                      >
                        {tag}
                      </span>
                    ))}
                  </>
                }
                footer={
                  sf.content ? (
                    <p className="line-clamp-2 text-xs text-ink-soft">
                      {truncate(sf.content.replace(/\s+/g, ' '), 100)}
                    </p>
                  ) : undefined
                }
                actions={[
                  { label: 'View details', href: `/dashboard/swipe-files/${sf.id}` },
                  {
                    label: confirmDeleteId === sf.id ? 'Confirm delete' : 'Delete',
                    onClick: () => handleDelete(sf.id),
                    variant: 'destructive',
                    disabled: deletingId === sf.id,
                    loading: deletingId === sf.id,
                    icon: deletingId === sf.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />,
                  },
                ]}
                href={`/dashboard/swipe-files/${sf.id}`}
              />
            ))}
          </div>
        )}
      </div>
    </PageShell>
  );
}
