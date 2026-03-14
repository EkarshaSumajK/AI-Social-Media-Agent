'use client';

import Link from 'next/link';
import { BookOpen, CheckCircle, FileText, Globe, Rss, ArrowRight } from 'lucide-react';

const STEPS = [
  {
    step: 1,
    icon: Rss,
    label: 'Collect & Screen Topics',
    desc: 'Pull trending topics from X, news feeds, and trusted sources. AI screens for relevance and trust score.',
    href: '/dashboard/topics',
    cta: 'Go to Topics',
    color: 'text-apple-blue border-apple-blue/20 bg-apple-blue/10',
    iconColor: 'text-apple-blue',
  },
  {
    step: 2,
    icon: FileText,
    label: 'Generate & Review Drafts',
    desc: 'AI writes a full 9-section article with SEO metadata and social captions. You review, edit, approve, or reject.',
    href: '/dashboard/drafts',
    cta: 'Go to Drafts',
    color: 'text-violet-400 border-violet-400/20 bg-violet-400/10',
    iconColor: 'text-violet-400',
  },
  {
    step: 3,
    icon: Globe,
    label: 'Publish & Share',
    desc: 'Approved drafts are published to your CMS. Social captions are pushed to connected platforms automatically.',
    href: '/dashboard/published',
    cta: 'View Published',
    color: 'text-emerald-400 border-emerald-500/20 bg-emerald-500/10',
    iconColor: 'text-emerald-400',
  },
] as const;

export default function ArticlePipelinePage() {
  return (
    <div className="flex min-h-[calc(100vh-4rem)] flex-col px-4 py-6 sm:px-6 lg:px-8">
      <header className="mb-10">
        <p className="text-xs font-semibold uppercase tracking-widest text-apple-blue/90">Article Pipeline</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-ink sm:text-4xl">
          Topic to Published Article
        </h1>
        <p className="mt-3 max-w-xl text-base text-ink-soft">
          AI collects trending topics, writes full SEO articles, and publishes to your CMS and social channels. You stay in control at every step.
        </p>
      </header>

      <section className="mb-10 grid gap-4 sm:grid-cols-3">
        {STEPS.map((step, index) => {
          const Icon = step.icon;
          return (
            <div key={step.step} className="relative flex flex-col">
              {index < STEPS.length - 1 && (
                <div className="absolute right-0 top-8 z-10 hidden translate-x-1/2 sm:block">
                  <ArrowRight size={16} className="text-ink-faint" />
                </div>
              )}
              <Link
                href={step.href}
                className="group flex flex-1 flex-col rounded-2xl border border-white/[0.06] bg-surface-2 p-6 transition-all duration-300 hover:-translate-y-1 hover:shadow-apple-lg"
              >
                <div className="mb-4 flex items-center gap-3">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-xl border ${step.color}`}>
                    <Icon size={20} />
                  </div>
                  <span className="text-xs font-semibold uppercase tracking-widest text-ink-faint">
                    Step {step.step}
                  </span>
                </div>
                <h2 className="mb-2 font-semibold text-ink">{step.label}</h2>
                <p className="flex-1 text-sm text-ink-soft leading-relaxed">{step.desc}</p>
                <div className={`mt-4 inline-flex items-center gap-1.5 text-sm font-medium ${step.iconColor}`}>
                  {step.cta} <ArrowRight size={14} />
                </div>
              </Link>
            </div>
          );
        })}
      </section>

      <section className="rounded-2xl border border-white/[0.06] bg-surface-2 p-6">
        <div className="mb-4 flex items-center gap-2">
          <BookOpen size={18} className="text-ink-faint" />
          <h2 className="font-semibold text-ink">How it works</h2>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { icon: CheckCircle, text: 'Topics screened by trust score and relevance AI' },
            { icon: CheckCircle, text: 'Duplicate detection blocks near-identical articles' },
            { icon: CheckCircle, text: '9-section article structure with SEO and readability checks' },
            { icon: CheckCircle, text: 'Social captions generated for Instagram, LinkedIn, X, Facebook' },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.text} className="flex items-start gap-2.5">
                <Icon size={15} className="mt-0.5 flex-shrink-0 text-emerald-400" />
                <p className="text-sm text-ink-soft">{item.text}</p>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
