'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  CalendarDays, Check, ChevronLeft, ChevronRight, Clock,
  Copy, Edit2, Loader2, Plus, Trash2, X,
} from 'lucide-react';

import { PageHeader } from '@/components/page-header';
import { CardListSkeleton } from '@/components/skeletons';
import { AppSelect } from '@/components/ui/app-select';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  createScheduledPost,
  deleteScheduledPost,
  fetchCalendarStats,
  fetchScheduledPosts,
  updateScheduledPost,
} from '@/lib/api';
import type { CalendarStats, ScheduledPost, ScheduledPostCreate } from '@/lib/types';
import { cn } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PLATFORMS = [
  { value: 'linkedin', label: 'LinkedIn', icon: '💼', color: 'border-blue-500/20 bg-blue-500/10 text-blue-400' },
  { value: 'twitter', label: 'X / Twitter', icon: '𝕏', color: 'border-sky-500/20 bg-sky-500/10 text-sky-400' },
  { value: 'instagram', label: 'Instagram', icon: '📸', color: 'border-pink-500/20 bg-pink-500/10 text-pink-400' },
  { value: 'youtube', label: 'YouTube', icon: '▶', color: 'border-red-500/20 bg-red-500/10 text-red-400' },
  { value: 'facebook', label: 'Facebook', icon: '📘', color: 'border-indigo-500/20 bg-indigo-500/10 text-indigo-400' },
];

const CONTENT_TYPES = [
  { value: 'post', label: 'Post' },
  { value: 'thread', label: 'Thread' },
  { value: 'reel', label: 'Reel / Short' },
  { value: 'story', label: 'Story' },
  { value: 'carousel', label: 'Carousel' },
  { value: 'video', label: 'Video' },
];

const STATUS_FILTERS = [
  { value: '', label: 'All' },
  { value: 'draft', label: 'Draft' },
  { value: 'scheduled', label: 'Scheduled' },
  { value: 'published', label: 'Published' },
  { value: 'failed', label: 'Failed' },
];

const PLATFORM_SELECT_OPTIONS = [
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'twitter', label: 'X / Twitter' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'youtube', label: 'YouTube' },
  { value: 'facebook', label: 'Facebook' },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatScheduled(iso: string | null) {
  if (!iso) return 'Not scheduled';
  return new Intl.DateTimeFormat('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  }).format(new Date(iso));
}

function getPlatformConfig(platform: string) {
  return PLATFORMS.find((p) => p.value === platform) ?? PLATFORMS[0];
}

function getStatusColor(status: string) {
  switch (status) {
    case 'scheduled': return 'border-apple-blue/20 bg-apple-blue/10 text-apple-blue';
    case 'published': return 'border-emerald-500/20 bg-emerald-500/10 text-emerald-400';
    case 'failed': return 'border-red-500/20 bg-red-500/10 text-red-400';
    default: return 'border-white/[0.08] bg-white/[0.04] text-ink-faint';
  }
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      onClick={() => {
        void navigator.clipboard.writeText(text).then(() => {
          setCopied(true);
          setTimeout(() => setCopied(false), 1800);
        });
      }}
      className="flex h-7 w-7 items-center justify-center rounded-md border border-white/[0.06] bg-white/[0.03] text-ink-faint transition hover:border-apple-blue/30 hover:bg-apple-blue/10 hover:text-apple-blue"
    >
      {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
    </button>
  );
}

// ---------------------------------------------------------------------------
// Calendar mini — week view
// ---------------------------------------------------------------------------

function getWeekDays(anchor: Date): Date[] {
  const monday = new Date(anchor);
  const day = monday.getDay();
  const diff = (day === 0 ? -6 : 1 - day);
  monday.setDate(monday.getDate() + diff);
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    return d;
  });
}

function isSameDay(a: Date, b: Date) {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

function WeekCalendar({
  posts,
  onDayClick,
  selectedDay,
}: {
  posts: ScheduledPost[];
  onDayClick: (d: Date) => void;
  selectedDay: Date | null;
}) {
  const [anchor, setAnchor] = useState(new Date());
  const days = getWeekDays(anchor);
  const today = new Date();

  const postsByDay = useMemo(() => {
    const map: Record<string, ScheduledPost[]> = {};
    for (const p of posts) {
      if (!p.scheduled_for) continue;
      const key = new Date(p.scheduled_for).toDateString();
      if (!map[key]) map[key] = [];
      map[key].push(p);
    }
    return map;
  }, [posts]);

  function prevWeek() {
    const d = new Date(anchor);
    d.setDate(d.getDate() - 7);
    setAnchor(d);
  }
  function nextWeek() {
    const d = new Date(anchor);
    d.setDate(d.getDate() + 7);
    setAnchor(d);
  }

  const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  return (
    <div className="rounded-xl border border-white/[0.06] bg-surface-2 overflow-hidden">
      <div className="flex items-center justify-between border-b border-white/[0.04] px-4 py-3">
        <p className="text-sm font-semibold text-ink">
          {days[0].toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} –{' '}
          {days[6].toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
        </p>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={prevWeek}
            className="flex h-7 w-7 items-center justify-center rounded-md border border-white/[0.06] text-ink-faint transition hover:border-white/[0.14] hover:text-ink"
          >
            <ChevronLeft size={14} />
          </button>
          <button
            type="button"
            onClick={() => setAnchor(new Date())}
            className="rounded-md border border-white/[0.06] px-2 py-1 text-[11px] text-ink-faint transition hover:border-white/[0.14] hover:text-ink"
          >
            Today
          </button>
          <button
            type="button"
            onClick={nextWeek}
            className="flex h-7 w-7 items-center justify-center rounded-md border border-white/[0.06] text-ink-faint transition hover:border-white/[0.14] hover:text-ink"
          >
            <ChevronRight size={14} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-7 divide-x divide-white/[0.04]">
        {days.map((day, i) => {
          const dayPosts = postsByDay[day.toDateString()] ?? [];
          const isToday = isSameDay(day, today);
          const isSelected = selectedDay ? isSameDay(day, selectedDay) : false;

          return (
            <button
              key={i}
              type="button"
              onClick={() => onDayClick(day)}
              className={cn(
                'flex min-h-[88px] flex-col gap-1 p-2 text-left transition',
                isSelected
                  ? 'bg-apple-blue/[0.06]'
                  : 'hover:bg-white/[0.03]',
              )}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-ink-faint">{DAY_LABELS[i]}</span>
                <span
                  className={cn(
                    'flex h-5 w-5 items-center justify-center rounded-full text-[11px] font-bold',
                    isToday ? 'bg-apple-blue text-white' : isSelected ? 'bg-apple-blue/20 text-apple-blue' : 'text-ink-soft',
                  )}
                >
                  {day.getDate()}
                </span>
              </div>
              <div className="flex flex-col gap-0.5 overflow-hidden">
                {dayPosts.slice(0, 3).map((p) => {
                  const pc = getPlatformConfig(p.platform);
                  return (
                    <div
                      key={p.id}
                      className={cn('truncate rounded px-1.5 py-0.5 text-[9px] font-medium border', pc.color)}
                    >
                      {pc.icon} {p.title.slice(0, 14)}
                    </div>
                  );
                })}
                {dayPosts.length > 3 && (
                  <span className="text-[9px] text-ink-faint">+{dayPosts.length - 3} more</span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// New post form
// ---------------------------------------------------------------------------

function NewPostForm({
  onCreated,
  prefillDate,
}: {
  onCreated: (post: ScheduledPost) => void;
  prefillDate?: Date | null;
}) {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [platform, setPlatform] = useState('linkedin');
  const [contentType, setContentType] = useState('post');
  const [scheduledFor, setScheduledFor] = useState(() => {
    if (prefillDate) {
      const d = new Date(prefillDate);
      d.setHours(9, 0, 0, 0);
      return d.toISOString().slice(0, 16);
    }
    return '';
  });
  const [hashtags, setHashtags] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || !content.trim()) {
      setError('Title and content are required.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const payload: ScheduledPostCreate = {
        title: title.trim(),
        content: content.trim(),
        platform,
        content_type: contentType,
        scheduled_for: scheduledFor ? new Date(scheduledFor).toISOString() : undefined,
        hashtags: hashtags.trim() ? hashtags.split(',').map((h) => h.trim()).filter(Boolean) : undefined,
      };
      const created = await createScheduledPost(payload);
      onCreated(created);
      setTitle('');
      setContent('');
      setHashtags('');
      setScheduledFor('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create post');
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={(e) => void handleSubmit(e)} className="flex flex-col gap-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <label className="mb-1.5 block text-sm font-medium text-ink">Title</label>
          <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Post title…" disabled={saving} />
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium text-ink">Platform</label>
          <AppSelect value={platform} onValueChange={setPlatform} options={PLATFORM_SELECT_OPTIONS} disabled={saving} />
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium text-ink">Content Type</label>
          <AppSelect value={contentType} onValueChange={setContentType} options={CONTENT_TYPES} disabled={saving} />
        </div>

        <div className="sm:col-span-2">
          <label className="mb-1.5 block text-sm font-medium text-ink">Content</label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Write your post content…"
            rows={5}
            disabled={saving}
            className="w-full resize-none rounded-lg border border-white/[0.08] bg-surface-2 px-3 py-2 text-sm text-ink placeholder:text-ink-faint focus:border-apple-blue/40 focus:outline-none focus:ring-0 disabled:opacity-50"
          />
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium text-ink">Schedule Date & Time</label>
          <input
            type="datetime-local"
            value={scheduledFor}
            onChange={(e) => setScheduledFor(e.target.value)}
            disabled={saving}
            className="h-10 w-full rounded-lg border border-white/[0.08] bg-surface-2 px-3 text-sm text-ink focus:border-apple-blue/40 focus:outline-none disabled:opacity-50"
          />
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium text-ink">Hashtags <span className="text-ink-faint">(comma-separated)</span></label>
          <Input value={hashtags} onChange={(e) => setHashtags(e.target.value)} placeholder="#marketing, #ai, #growth" disabled={saving} />
        </div>
      </div>

      {error && <p className="rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-400">{error}</p>}

      <Button type="submit" disabled={saving} className="w-full sm:w-fit">
        {saving ? <><Loader2 size={14} className="mr-2 animate-spin" /> Saving...</> : <><Plus size={14} className="mr-2" /> Add to Calendar</>}
      </Button>
    </form>
  );
}

// ---------------------------------------------------------------------------
// Post card
// ---------------------------------------------------------------------------

function PostCard({
  post,
  onDelete,
  onStatusChange,
}: {
  post: ScheduledPost;
  onDelete: (id: number) => void;
  onStatusChange: (id: number, status: string) => void;
}) {
  const [deleting, setDeleting] = useState(false);
  const [updating, setUpdating] = useState(false);
  const pc = getPlatformConfig(post.platform);

  async function handleDelete() {
    setDeleting(true);
    try {
      await deleteScheduledPost(post.id);
      onDelete(post.id);
    } finally {
      setDeleting(false);
    }
  }

  async function markPublished() {
    setUpdating(true);
    try {
      await updateScheduledPost(post.id, { status: 'published' });
      onStatusChange(post.id, 'published');
    } finally {
      setUpdating(false);
    }
  }

  return (
    <article className="group rounded-xl border border-white/[0.06] bg-surface-2 p-4 transition hover:border-white/[0.12]">
      <div className="mb-3 flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="mb-1.5 flex flex-wrap items-center gap-2">
            <span className={cn('rounded-full border px-2 py-0.5 text-[10px] font-semibold', pc.color)}>
              {pc.icon} {pc.label}
            </span>
            <span className="rounded-full border border-white/[0.06] bg-white/[0.03] px-2 py-0.5 text-[10px] text-ink-faint capitalize">
              {post.content_type}
            </span>
            <span className={cn('rounded-full border px-2 py-0.5 text-[10px] font-semibold capitalize', getStatusColor(post.status))}>
              {post.status}
            </span>
          </div>
          <p className="font-semibold text-ink line-clamp-1">{post.title}</p>
        </div>
        <div className="flex items-center gap-1 opacity-0 transition group-hover:opacity-100">
          <CopyButton text={post.content} />
          {post.status !== 'published' && (
            <button
              type="button"
              onClick={() => void markPublished()}
              disabled={updating}
              title="Mark as published"
              className="flex h-7 w-7 items-center justify-center rounded-md border border-white/[0.06] bg-white/[0.03] text-ink-faint transition hover:border-emerald-500/30 hover:bg-emerald-500/10 hover:text-emerald-400"
            >
              {updating ? <Loader2 size={13} className="animate-spin" /> : <Check size={13} />}
            </button>
          )}
          <button
            type="button"
            onClick={() => void handleDelete()}
            disabled={deleting}
            title="Delete"
            className="flex h-7 w-7 items-center justify-center rounded-md border border-white/[0.06] bg-white/[0.03] text-ink-faint transition hover:border-red-500/30 hover:bg-red-500/10 hover:text-red-400"
          >
            {deleting ? <Loader2 size={13} className="animate-spin" /> : <Trash2 size={13} />}
          </button>
        </div>
      </div>

      <p className="mb-3 line-clamp-2 text-sm text-ink-soft">{post.content}</p>

      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-ink-faint">
        <div className="flex items-center gap-1.5">
          <Clock size={11} />
          <span>{formatScheduled(post.scheduled_for ?? null)}</span>
        </div>
        {post.hashtags && post.hashtags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {post.hashtags.slice(0, 3).map((h) => (
              <span key={h} className="rounded border border-white/[0.06] bg-white/[0.03] px-1.5 py-0.5 text-[10px] text-apple-blue/70">
                {h.startsWith('#') ? h : `#${h}`}
              </span>
            ))}
            {post.hashtags.length > 3 && <span className="text-ink-faint">+{post.hashtags.length - 3}</span>}
          </div>
        )}
      </div>
    </article>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function SchedulingPage() {
  const [posts, setPosts] = useState<ScheduledPost[]>([]);
  const [stats, setStats] = useState<CalendarStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [platformFilter, setPlatformFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [selectedDay, setSelectedDay] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const [postsData, statsData] = await Promise.all([
        fetchScheduledPosts({ platform: platformFilter || undefined, status: statusFilter || undefined }),
        fetchCalendarStats(),
      ]);
      setPosts(postsData);
      setStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void loadData(); }, [statusFilter, platformFilter]);

  function handlePostCreated(post: ScheduledPost) {
    setPosts((prev) => [post, ...prev]);
    setStats((prev) => prev ? { ...prev, total: prev.total + 1, [post.status]: (prev[post.status as keyof CalendarStats] as number) + 1 } : prev);
    setShowForm(false);
  }

  function handlePostDeleted(id: number) {
    setPosts((prev) => prev.filter((p) => p.id !== id));
  }

  function handleStatusChange(id: number, status: string) {
    setPosts((prev) => prev.map((p) => p.id === id ? { ...p, status } : p));
  }

  const dayPosts = useMemo(() => {
    if (!selectedDay) return posts;
    return posts.filter((p) => p.scheduled_for && isSameDay(new Date(p.scheduled_for), selectedDay));
  }, [posts, selectedDay]);

  const displayPosts = selectedDay ? dayPosts : posts;

  return (
    <div className="flex flex-col gap-6 p-4 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          eyebrow="Automation"
          title="Content Calendar"
          description="Schedule, manage, and track your content across all platforms"
        />
        <Button onClick={() => setShowForm(!showForm)} className="flex-shrink-0">
          {showForm ? <><X size={14} className="mr-2" /> Cancel</> : <><Plus size={14} className="mr-2" /> New Post</>}
        </Button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          {[
            { label: 'Total', value: stats.total, color: 'text-ink' },
            { label: 'Scheduled', value: stats.scheduled, color: 'text-apple-blue' },
            { label: 'Draft', value: stats.draft, color: 'text-ink-soft' },
            { label: 'Published', value: stats.published, color: 'text-emerald-400' },
            { label: 'Failed', value: stats.failed, color: 'text-red-400' },
          ].map(({ label, value, color }) => (
            <Card key={label} className="p-4">
              <p className="text-[10px] uppercase tracking-[0.2em] text-ink-faint">{label}</p>
              <p className={cn('mt-1.5 text-2xl font-bold', color)}>{value}</p>
            </Card>
          ))}
        </div>
      )}

      {/* New Post Form */}
      {showForm && (
        <Card className="p-5">
          <h2 className="mb-4 text-base font-semibold text-ink">New Scheduled Post</h2>
          <NewPostForm onCreated={handlePostCreated} prefillDate={selectedDay} />
        </Card>
      )}

      {/* Week Calendar */}
      <WeekCalendar
        posts={posts}
        onDayClick={(d) => setSelectedDay((prev) => (prev && isSameDay(prev, d) ? null : d))}
        selectedDay={selectedDay}
      />

      {/* Filters + list */}
      <div>
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1 rounded-lg border border-white/[0.08] bg-surface-2 p-1 text-xs">
            {STATUS_FILTERS.map((f) => (
              <button
                key={f.value}
                type="button"
                onClick={() => setStatusFilter(f.value)}
                className={cn(
                  'rounded-md px-3 py-1.5 font-medium transition',
                  statusFilter === f.value ? 'bg-apple-blue/10 text-apple-blue' : 'text-ink-faint hover:text-ink',
                )}
              >
                {f.label}
              </button>
            ))}
          </div>

          <div className="w-40">
            <AppSelect
              value={platformFilter}
              onValueChange={setPlatformFilter}
              options={[{ value: '', label: 'All Platforms' }, ...PLATFORM_SELECT_OPTIONS]}
            />
          </div>

          {selectedDay && (
            <div className="flex items-center gap-2 rounded-lg border border-apple-blue/20 bg-apple-blue/10 px-3 py-1.5 text-xs text-apple-blue">
              <CalendarDays size={12} />
              {selectedDay.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
              <button type="button" onClick={() => setSelectedDay(null)} className="hover:text-apple-blue/60">
                <X size={11} />
              </button>
            </div>
          )}
        </div>

        {error && (
          <p className="mb-4 rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-400">{error}</p>
        )}

        {loading ? (
          <CardListSkeleton count={4} />
        ) : displayPosts.length === 0 ? (
          <div className="flex flex-col items-center gap-3 rounded-xl border border-white/[0.06] bg-surface-2 py-16 text-center">
            <CalendarDays size={36} className="text-ink-faint" />
            <p className="text-sm font-medium text-ink-soft">No posts here yet</p>
            <p className="text-xs text-ink-faint">
              {selectedDay ? 'No posts scheduled for this day.' : 'Click "New Post" to add your first scheduled post.'}
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {displayPosts.map((post) => (
              <PostCard
                key={post.id}
                post={post}
                onDelete={handlePostDeleted}
                onStatusChange={handleStatusChange}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
