'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { useState } from 'react';

import { PageHeader } from '@/components/page-header';
import { PageShell } from '@/components/page-shell';
import { AppSelect } from '@/components/ui/app-select';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { createCampaign } from '@/lib/api';
import { PLATFORMS, SOCIAL_PLATFORMS } from '@/lib/types';

const SOCIAL_PLATFORM_LABELS: Record<string, string> = {
  linkedin: 'LinkedIn',
  instagram: 'Instagram',
  twitter: 'X (Twitter)',
  facebook: 'Facebook',
  youtube: 'YouTube',
};

export default function CreateCampaignPage() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [goal, setGoal] = useState('lead generation');
  const [audience, setAudience] = useState('founders and marketers');
  const [eventDate, setEventDate] = useState('');
  const [platformEntity, setPlatformEntity] = useState<string>('horizon');
  const [platforms, setPlatforms] = useState<string[]>(['linkedin', 'twitter']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function togglePlatform(value: string) {
    setPlatforms((prev) =>
      prev.includes(value) ? prev.filter((p) => p !== value) : [...prev, value]
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmedTitle = title.trim();
    const trimmedGoal = goal.trim();
    const trimmedAudience = audience.trim();

    if (!trimmedTitle) {
      setError('Please enter a campaign title.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const campaign = await createCampaign({
        title: trimmedTitle,
        event_date: eventDate || undefined,
        goal: trimmedGoal || undefined,
        audience: trimmedAudience || undefined,
        platforms: platforms.length ? platforms : undefined,
        platform_entity: platformEntity,
      });
      router.push(`/dashboard/campaigns/${campaign.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create campaign');
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageShell>
      <PageHeader title="New Campaign" description="Create a campaign plan">
        <Button asChild variant="outline" size="sm">
          <Link href="/dashboard/campaigns">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to list
          </Link>
        </Button>
      </PageHeader>

      <div className="px-4 sm:px-6 lg:px-8">
        {error && (
          <div className="mb-6 rounded-lg border border-ember/30 bg-ember/5 px-4 py-3 text-sm text-ember">
            {error}
          </div>
        )}

        <Card className="max-w-2xl border-white/[0.06] bg-card">
          <CardHeader>
            <h2 className="text-base font-semibold text-ink">Campaign details</h2>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="grid gap-4 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <label className="mb-1.5 block text-sm font-medium text-ink">Title</label>
                <Input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Webinar on AI GTM"
                  disabled={loading}
                  className="border-white/[0.08] bg-white/[0.03]"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-ink">Goal</label>
                <Input
                  value={goal}
                  onChange={(e) => setGoal(e.target.value)}
                  placeholder="e.g. lead generation"
                  disabled={loading}
                  className="border-white/[0.08] bg-white/[0.03]"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-ink">Event date (optional)</label>
                <Input
                  type="date"
                  value={eventDate}
                  onChange={(e) => setEventDate(e.target.value)}
                  disabled={loading}
                  className="border-white/[0.08] bg-white/[0.03]"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="mb-1.5 block text-sm font-medium text-ink">Audience</label>
                <Input
                  value={audience}
                  onChange={(e) => setAudience(e.target.value)}
                  placeholder="e.g. founders, GTM leaders"
                  disabled={loading}
                  className="border-white/[0.08] bg-white/[0.03]"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-ink">Platform entity</label>
                <AppSelect
                  value={platformEntity}
                  onValueChange={setPlatformEntity}
                  disabled={loading}
                  options={PLATFORMS.map((p) => ({ value: p.value, label: p.label }))}
                />
              </div>
              <div className="sm:col-span-2">
                <label className="mb-2 block text-sm font-medium text-ink">Target social platforms</label>
                <div className="flex flex-wrap gap-2">
                  {SOCIAL_PLATFORMS.map((platform) => (
                    <label
                      key={platform}
                      className="flex cursor-pointer items-center gap-2 rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-2 text-sm transition-colors hover:border-apple-blue/30 has-[:checked]:border-apple-blue/40 has-[:checked]:bg-apple-blue/10"
                    >
                      <input
                        type="checkbox"
                        checked={platforms.includes(platform)}
                        onChange={() => togglePlatform(platform)}
                        disabled={loading}
                        className="h-4 w-4 rounded border-white/[0.08] bg-transparent text-apple-blue"
                      />
                      <span className="text-ink">
                        {SOCIAL_PLATFORM_LABELS[platform] || platform}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
              <div className="sm:col-span-2">
                <Button type="submit" disabled={loading}>
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    'Create Campaign'
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </PageShell>
  );
}
