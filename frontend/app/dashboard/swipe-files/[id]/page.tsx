'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ArrowLeft, ExternalLink, Loader2, Trash2 } from 'lucide-react';

import { PageHeader } from '@/components/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { deleteSwipeFile, fetchSwipeFile } from '@/lib/api';
import type { SwipeFile } from '@/lib/types';

export default function SwipeFileDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const swipeId = Number(params.id);

  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [swipeFile, setSwipeFile] = useState<SwipeFile | null>(null);

  useEffect(() => {
    async function loadSwipeFile() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchSwipeFile(swipeId);
        setSwipeFile(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load swipe file');
      } finally {
        setLoading(false);
      }
    }

    if (Number.isNaN(swipeId)) {
      setLoading(false);
      setError('Invalid swipe file id');
      return;
    }

    void loadSwipeFile();
  }, [swipeId]);

  async function handleDelete() {
    if (!swipeFile) return;
    if (!confirmDelete) {
      setConfirmDelete(true);
      return;
    }
    setDeleting(true);
    setError(null);
    try {
      await deleteSwipeFile(swipeFile.id);
      router.push('/dashboard/swipe-files');
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete swipe file');
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="flex flex-col">
      <PageHeader title={swipeFile?.title || 'Swipe File Detail'} description="Complete swipe file content and metadata">
        <Button asChild variant="outline" size="sm">
          <Link href="/dashboard/swipe-files">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to swipe files
          </Link>
        </Button>
      </PageHeader>

      <div className="flex flex-col gap-6 p-4 sm:p-6">
        {error && <div className="rounded-xl border border-ember/30 bg-ember/5 px-4 py-3 text-sm text-ember">{error}</div>}

        {loading ? (
          <div className="flex items-center gap-2 text-sm text-ink-soft">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading swipe file...
          </div>
        ) : swipeFile ? (
          <>
            <section className="rounded-lg border bg-card p-5 text-card-foreground shadow-sm">
              <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
                <h2 className="text-lg font-semibold text-ink">{swipeFile.title}</h2>
                <div className="flex flex-wrap gap-2">
                  {swipeFile.source_url && (
                    <Button asChild variant="outline" size="sm">
                      <a href={swipeFile.source_url} target="_blank" rel="noreferrer">
                        <ExternalLink className="mr-2 h-4 w-4" />
                        Open source
                      </a>
                    </Button>
                  )}
                  <Button type="button" variant="destructive" size="sm" onClick={handleDelete} disabled={deleting}>
                    {deleting ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Deleting...
                      </>
                    ) : (
                      <>
                        <Trash2 className="mr-2 h-4 w-4" />
                        {confirmDelete ? 'Confirm delete' : 'Delete'}
                      </>
                    )}
                  </Button>
                </div>
              </div>

              <div className="mb-4 flex flex-wrap items-center gap-2">
                <Badge variant="secondary">{swipeFile.platform}</Badge>
                {swipeFile.tags?.map((tag) => (
                  <Badge key={tag} variant="outline">
                    {tag}
                  </Badge>
                ))}
              </div>

              <article className="rounded-lg border border-white/[0.06] bg-surface-2 p-4">
                <p className="whitespace-pre-wrap break-words text-sm text-ink">{swipeFile.content}</p>
              </article>
            </section>

            <section className="rounded-lg border bg-card p-5 text-card-foreground shadow-sm">
              <h2 className="mb-3 text-lg font-semibold text-ink">Performance notes</h2>
              {swipeFile.performance_notes ? (
                <p className="whitespace-pre-wrap break-words text-sm text-ink">{swipeFile.performance_notes}</p>
              ) : (
                <p className="text-sm text-ink-soft">No performance notes added.</p>
              )}
            </section>
          </>
        ) : (
          <p className="text-sm text-ink-soft">Swipe file not found.</p>
        )}
      </div>
    </div>
  );
}
