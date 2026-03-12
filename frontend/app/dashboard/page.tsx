'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import {
  BarChart3,
  BookOpen,
  CalendarDays,
  Flame,
  Globe,
  Lightbulb,
  Megaphone,
  Newspaper,
  Repeat,
  Shield,
  Target,
} from 'lucide-react';

import { cn } from '@/lib/utils';

const FLOWS = [
  { href: '/dashboard/flows/trending-post', label: 'Trending Now', icon: Flame, desc: 'Turn trending topics into posts' },
  { href: '/dashboard/daily-posts', label: 'Daily Post Suggestions', icon: Newspaper, desc: 'What to post today' },
  { href: '/dashboard/flows/webinar', label: 'Event / Webinar Builder', icon: Megaphone, desc: 'Full campaign from pre to post' },
  { href: '/dashboard/thought-leadership', label: 'Thought Leadership', icon: Lightbulb, desc: 'Position as an expert' },
  { href: '/dashboard/audience-content', label: 'Audience Content', icon: Target, desc: 'Content by audience & stage' },
  { href: '/dashboard/platform-content', label: 'Platform Generator', icon: Globe, desc: 'LinkedIn, Instagram, X, YouTube' },
  { href: '/dashboard/repurpose', label: 'Repurpose Content', icon: Repeat, desc: 'Turn long-form into many posts' },
  { href: '/dashboard/scheduling', label: 'Automation & Scheduling', icon: CalendarDays, desc: 'Schedule & publish' },
  { href: '/dashboard/competitors', label: 'Competitor Insights', icon: Shield, desc: 'Track & improve on competitors' },
  { href: '/dashboard/performance', label: 'Performance Analytics', icon: BarChart3, desc: 'See what works' },
  { href: '/dashboard/article-pipeline', label: 'Article Pipeline', icon: BookOpen, desc: 'Topic to published article' },
] as const;

interface HealthStatus {
  backend: boolean;
  redis: boolean;
  celery: boolean;
}

function StatusDot({ ok, label }: { ok: boolean; label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className={cn('h-2 w-2 rounded-full', ok ? 'bg-emerald-400' : 'bg-red-400')} />
      <span className={cn('text-xs', ok ? 'text-ink-soft' : 'text-red-400')}>{label}</span>
    </div>
  );
}

function HealthBar() {
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1'}/health`)
      .then((r) => r.json())
      .then((d) => setHealth({ backend: true, redis: d.redis ?? false, celery: d.celery ?? false }))
      .catch(() => setHealth({ backend: false, redis: false, celery: false }));
  }, []);

  if (!health) return null;

  const allOk = health.backend && health.redis && health.celery;

  if (allOk) return null;

  return (
    <div className="mb-6 flex flex-wrap items-center gap-4 rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3">
      <span className="text-xs font-semibold text-red-400">Services down — some features won't work</span>
      <div className="flex flex-wrap gap-4">
        <StatusDot ok={health.backend} label="Backend" />
        <StatusDot ok={health.redis} label="Redis" />
        <StatusDot ok={health.celery} label="Celery Worker" />
      </div>
      {!health.celery && (
        <span className="text-xs text-ink-faint">
          Start with: <code className="rounded bg-white/[0.05] px-1 py-0.5 text-[11px]">start.bat</code>
        </span>
      )}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <div className="flex min-h-[calc(100vh-4rem)] flex-col px-4 py-6 sm:px-6 lg:px-8">
      <header className="mb-12">
        <p className="text-xs font-semibold uppercase tracking-widest text-apple-blue/90">Content Platform</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-ink sm:text-5xl">
          Choose a flow.
        </h1>
        <p className="mt-4 max-w-xl text-lg text-ink-soft font-medium">
          Review, approve, publish. AI handles strategy, trends, and copy.
        </p>
      </header>

      <HealthBar />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {FLOWS.map((flow) => {
          const Icon = flow.icon;
          return (
            <Link
              key={flow.href}
              href={flow.href}
              className={cn(
                'group flex flex-col rounded-2xl p-6 transition-all duration-500 ease-[cubic-bezier(0.175,0.885,0.32,1.275)]',
                'apple-glass hover:shadow-apple-lg hover:-translate-y-1',
              )}
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-surface-2 to-surface border border-white/5 text-ink-faint shadow-sm transition-colors group-hover:text-apple-blue group-hover:border-apple-blue/30">
                <Icon size={24} strokeWidth={1.5} />
              </div>
              <h2 className="mt-5 font-semibold text-ink tracking-tight">{flow.label}</h2>
              <p className="mt-2 text-sm text-ink-soft leading-relaxed">{flow.desc}</p>
            </Link>
          );
        })}
      </section>
    </div>
  );
}
