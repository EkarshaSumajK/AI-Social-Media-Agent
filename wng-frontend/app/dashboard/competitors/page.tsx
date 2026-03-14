'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Loader2, Plus } from 'lucide-react';
import { useEffect, useState } from 'react';

import { ListCard } from '@/components/list-card';
import { PageHeader } from '@/components/page-header';
import { PageShell } from '@/components/page-shell';
import { AppSelect } from '@/components/ui/app-select';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { addCompetitor, fetchCompetitors } from '@/lib/api';
import type { Competitor } from '@/lib/types';
import { PLATFORMS, SOCIAL_PLATFORMS } from '@/lib/types';

const SOCIAL_PLATFORM_LABELS: Record<string, string> = {
  linkedin: 'LinkedIn',
  instagram: 'Instagram',
  twitter: 'X (Twitter)',
  facebook: 'Facebook',
  youtube: 'YouTube',
};

export default function CompetitorsPage() {
  const router = useRouter();
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addOpen, setAddOpen] = useState(false);

  const [name, setName] = useState('');
  const [profileUrl, setProfileUrl] = useState('');
  const [platform, setPlatform] = useState<string>('linkedin');
  const [platformEntity, setPlatformEntity] = useState<string>('horizon');
  const [submitting, setSubmitting] = useState(false);

  async function loadCompetitors() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCompetitors();
      setCompetitors(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load competitors');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadCompetitors();
  }, []);

  async function handleAdd(event: React.FormEvent) {
    event.preventDefault();
    const trimmedName = name.trim();
    const trimmedProfileUrl = profileUrl.trim();

    if (!trimmedName || !trimmedProfileUrl) {
      setError('Name and profile URL are required.');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const created = await addCompetitor({
        name: trimmedName,
        platform,
        profile_url: trimmedProfileUrl,
        platform_entity: platformEntity,
      });
      setName('');
      setProfileUrl('');
      setAddOpen(false);
      await loadCompetitors();
      router.push(`/dashboard/competitors/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add competitor');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <PageShell>
      <PageHeader
        title="Competitor Insights"
        description="Track competitors and run LLM analysis"
      >
        <Dialog open={addOpen} onOpenChange={setAddOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Add Competitor
            </Button>
          </DialogTrigger>
          <DialogContent className="border-white/[0.06] bg-card sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>Add competitor</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleAdd} className="grid gap-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-ink">Name</label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Acme Marketing"
                  disabled={submitting}
                  className="border-white/[0.08] bg-white/[0.03]"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-ink">Profile URL</label>
                <Input
                  type="url"
                  value={profileUrl}
                  onChange={(e) => setProfileUrl(e.target.value)}
                  placeholder="https://..."
                  disabled={submitting}
                  className="border-white/[0.08] bg-white/[0.03]"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-ink">Social platform</label>
                <AppSelect
                  value={platform}
                  onValueChange={setPlatform}
                  disabled={submitting}
                  options={SOCIAL_PLATFORMS.map((item) => ({
                    value: item.value,
                    label: item.label,
                  }))}
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-ink">Platform entity</label>
                <AppSelect
                  value={platformEntity}
                  onValueChange={setPlatformEntity}
                  disabled={submitting}
                  options={PLATFORMS.map((item) => ({
                    value: item.value,
                    label: item.label,
                  }))}
                />
              </div>
              <Button type="submit" disabled={submitting}>
                {submitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Adding...
                  </>
                ) : (
                  'Add Competitor'
                )}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </PageHeader>

      <div className="flex flex-col gap-6 px-4 sm:px-6 lg:px-8">
        {error && (
          <div className="rounded-lg border border-ember/30 bg-ember/5 px-4 py-3 text-sm text-ember">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center gap-2 py-12 text-sm text-ink-soft">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading competitors...
          </div>
        ) : competitors.length === 0 ? (
          <div className="flex flex-col items-center gap-4 rounded-lg border border-dashed border-white/[0.08] bg-white/[0.02] py-16">
            <p className="text-sm text-ink-soft">No competitors yet. Add one to get started.</p>
            <Button onClick={() => setAddOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Add Competitor
            </Button>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {competitors.map((competitor) => (
              <ListCard
                key={competitor.id}
                title={competitor.name}
                metadata={
                  <>
                    <span>{competitor.platform_entity}</span>
                    <span>•</span>
                    <span>{SOCIAL_PLATFORM_LABELS[competitor.platform] || competitor.platform}</span>
                  </>
                }
                tags={
                  <>
                    <span className="rounded-md border border-apple-blue/20 bg-apple-blue/10 px-2 py-0.5 text-xs font-medium text-apple-blue">
                      {SOCIAL_PLATFORM_LABELS[competitor.platform] || competitor.platform}
                    </span>
                    <span className="rounded-md border border-white/[0.06] bg-white/[0.04] px-2 py-0.5 text-xs text-ink-soft">
                      {competitor.platform_entity}
                    </span>
                  </>
                }
                actions={[
                  { label: 'View details', href: `/dashboard/competitors/${competitor.id}` },
                ]}
                href={`/dashboard/competitors/${competitor.id}`}
              />
            ))}
          </div>
        )}
      </div>
    </PageShell>
  );
}
