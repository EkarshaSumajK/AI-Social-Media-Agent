'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';

/** Maps route segments (after /dashboard/) to human-readable labels. */
const SEGMENT_LABELS: Record<string, string> = {
  topics: 'Topics Pipeline',
  drafts: 'Draft Queue',
  published: 'Published',
  'daily-posts': 'Daily Posts',
  'thought-leadership': 'Thought Leadership',
  'audience-content': 'Audience Content',
  'platform-content': 'Platform Generator',
  repurpose: 'Repurpose',
  campaigns: 'Campaigns',
  competitors: 'Competitors',
  hooks: 'Hook Library',
  'swipe-files': 'Swipe Files',
  paraphraser: 'Paraphraser',
  scoring: 'Content Scoring',
  performance: 'Performance',
  audit: 'Audit Log',
  onboarding: 'Setup',
  flows: 'Flows',
  'trending-post': 'Trending Now',
  webinar: 'Event Builder',
  'competitor-intel': 'Competitor Intel',
  'youtube-shorts': 'YouTube Shorts',
  create: 'Create',
  history: 'History',
};

/** Maps parent segments to the prefix used for dynamic [id] child routes. */
const DYNAMIC_PREFIXES: Record<string, string> = {
  drafts: 'Draft',
  campaigns: 'Campaign',
  competitors: 'Competitor',
  hooks: 'Hook',
  'swipe-files': 'Swipe File',
  'daily-posts': 'Batch',
  history: 'Post',
};

export function DashboardBreadcrumbs() {
  const pathname = usePathname();

  // Don't render breadcrumbs on the root dashboard page
  if (!pathname || pathname === '/dashboard' || pathname === '/dashboard/') {
    return null;
  }

  // Strip /dashboard/ prefix and split into segments
  const rawSegments = pathname.replace(/^\/dashboard\/?/, '').split('/').filter(Boolean);

  if (rawSegments.length === 0) {
    return null;
  }

  // Build breadcrumb entries
  const crumbs: { label: string; href?: string }[] = [];

  for (let i = 0; i < rawSegments.length; i++) {
    const segment = rawSegments[i];
    const parentSegment = i > 0 ? rawSegments[i - 1] : null;

    // Check if this is a dynamic [id] segment (numeric or UUID-like)
    const isDynamic = /^\d+$/.test(segment) || /^[a-f0-9-]{8,}$/i.test(segment);

    if (isDynamic && parentSegment && DYNAMIC_PREFIXES[parentSegment]) {
      crumbs.push({ label: `${DYNAMIC_PREFIXES[parentSegment]} #${segment}` });
    } else {
      const label = SEGMENT_LABELS[segment] ?? segment;
      // If this is not the last segment, it should be a link
      if (i < rawSegments.length - 1) {
        const href = '/dashboard/' + rawSegments.slice(0, i + 1).join('/');
        crumbs.push({ label, href });
      } else {
        crumbs.push({ label });
      }
    }
  }

  return (
    <Breadcrumb>
      <BreadcrumbList>
        <BreadcrumbItem>
          <BreadcrumbLink asChild>
            <Link href="/dashboard" className="text-ink-faint hover:text-ink-soft">
              Command Center
            </Link>
          </BreadcrumbLink>
        </BreadcrumbItem>

        {crumbs.map((crumb, index) => (
          <span key={index} className="contents">
            <BreadcrumbSeparator className="text-ink-faint/50" />
            <BreadcrumbItem>
              {crumb.href ? (
                <BreadcrumbLink asChild>
                  <Link href={crumb.href} className="text-ink-faint hover:text-ink-soft">
                    {crumb.label}
                  </Link>
                </BreadcrumbLink>
              ) : (
                <BreadcrumbPage className="text-ink-soft font-medium">
                  {crumb.label}
                </BreadcrumbPage>
              )}
            </BreadcrumbItem>
          </span>
        ))}
      </BreadcrumbList>
    </Breadcrumb>
  );
}
