'use client';

import { useEffect, useState } from 'react';
import { Loader2, ExternalLink, Globe } from 'lucide-react';

import { PageHeader } from '@/components/page-header';
import { fetchPublished } from '@/lib/api';
import type { PublishedArticle } from '@/lib/types';

export default function PublishedPage() {
  const [articles, setArticles] = useState<PublishedArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await fetchPublished();
        setArticles(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load published articles');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="flex flex-col">
      <PageHeader title="Published Articles" description="Live content across all platforms">
        <span className="text-xs text-ink-soft">{articles.length} articles</span>
      </PageHeader>

      <div className="flex flex-col gap-4 p-4 sm:p-6">
        {error && <div className="rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-2.5 text-sm text-red-400">{error}</div>}

        {loading ? (
          <div className="flex items-center gap-2 py-12 text-sm text-ink-soft"><Loader2 size={16} className="animate-spin" /> Loading...</div>
        ) : (
          <div className="space-y-3">
            {articles.map((article) => (
              <div key={article.id} className="rounded-lg border bg-card text-card-foreground shadow-sm p-5">
                <div className="mb-2 flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-ink">{article.seo_title}</p>
                    <p className="mt-1 text-sm text-ink-soft">{article.meta_description}</p>
                  </div>
                  <span className="flex-shrink-0 rounded-lg bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 text-xs font-medium text-emerald-400">
                    Published
                  </span>
                </div>

                <div className="mb-3 flex flex-wrap items-center gap-2">
                  <span className="rounded-md bg-apple-blue/10 px-2 py-0.5 text-xs text-apple-blue">{article.platform}</span>
                  {article.keywords?.slice(0, 5).map((kw) => (
                    <span key={kw} className="rounded-md bg-surface-3 px-2 py-0.5 text-[11px] text-ink-soft">{kw}</span>
                  ))}
                </div>

                <div className="flex items-center gap-4 text-xs text-ink-soft">
                  {article.published_at && <span>{new Date(article.published_at).toLocaleString()}</span>}
                  {article.published_url && (
                    <a href={article.published_url} rel="noreferrer" target="_blank" className="inline-flex items-center gap-1 font-medium text-apple-blue/80 hover:text-apple-blue hover:underline">
                      <ExternalLink size={12} /> View Live
                    </a>
                  )}
                  {article.slug && (
                    <span className="inline-flex items-center gap-1 text-ink-faint">
                      <Globe size={12} /> /{article.slug}
                    </span>
                  )}
                </div>
              </div>
            ))}
            {articles.length === 0 && (
              <div className="py-12 text-center">
                <Globe size={40} className="mx-auto mb-3 text-ink-faint" />
                <p className="text-sm text-ink-soft">No published articles yet.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
