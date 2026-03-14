'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  AlertCircle, CheckCircle2, ExternalLink, Loader2, RefreshCw,
  Settings, Trash2, WifiOff,
} from 'lucide-react';

import { PageHeader } from '@/components/page-header';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { fetchSocialAccounts, removeSocialAccount, startSocialOAuth } from '@/lib/api';
import type { SocialAccount } from '@/lib/types';
import { cn } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Platform config
// ---------------------------------------------------------------------------

const PLATFORMS = [
  {
    id: 'linkedin',
    label: 'LinkedIn',
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5 fill-current" aria-hidden>
        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
      </svg>
    ),
    description: 'Authority posts, articles, carousels & polls',
    color: 'hover:border-blue-500/40',
    connected: 'border-blue-500/40 bg-blue-500/5',
    badge: 'border-blue-500/20 bg-blue-500/10 text-blue-400',
    dot: 'bg-blue-400',
    docsUrl: 'https://developer.linkedin.com/docs/v2/oauth2-client-credentials-flow',
    envKey: 'LINKEDIN_CLIENT_ID',
  },
  {
    id: 'twitter',
    label: 'X / Twitter',
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5 fill-current" aria-hidden>
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.746l7.73-8.835L1.254 2.25H8.08l4.253 5.622zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
      </svg>
    ),
    description: 'Threads, viral hooks & real-time debates',
    color: 'hover:border-sky-500/40',
    connected: 'border-sky-500/40 bg-sky-500/5',
    badge: 'border-sky-500/20 bg-sky-500/10 text-sky-400',
    dot: 'bg-sky-400',
    docsUrl: 'https://developer.twitter.com/en/docs/authentication/oauth-2-0',
    envKey: 'TWITTER_CLIENT_ID',
  },
  {
    id: 'instagram',
    label: 'Instagram',
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5 fill-current" aria-hidden>
        <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 1 0 0 12.324 6.162 6.162 0 0 0 0-12.324zM12 16a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm6.406-11.845a1.44 1.44 0 1 0 0 2.881 1.44 1.44 0 0 0 0-2.881z" />
      </svg>
    ),
    description: 'Reels, carousels & story sequences',
    color: 'hover:border-pink-500/40',
    connected: 'border-pink-500/40 bg-pink-500/5',
    badge: 'border-pink-500/20 bg-pink-500/10 text-pink-400',
    dot: 'bg-pink-400',
    docsUrl: 'https://developers.facebook.com/docs/instagram-api/getting-started',
    envKey: 'FACEBOOK_APP_ID',
  },
  {
    id: 'youtube',
    label: 'YouTube',
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5 fill-current" aria-hidden>
        <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
      </svg>
    ),
    description: 'Shorts, long-form videos & channel management',
    color: 'hover:border-red-500/40',
    connected: 'border-red-500/40 bg-red-500/5',
    badge: 'border-red-500/20 bg-red-500/10 text-red-400',
    dot: 'bg-red-400',
    docsUrl: 'https://developers.google.com/youtube/v3/guides/auth/client-side-web-apps',
    envKey: 'GOOGLE_CLIENT_ID',
  },
  {
    id: 'facebook',
    label: 'Facebook',
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5 fill-current" aria-hidden>
        <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
      </svg>
    ),
    description: 'Posts, pages, groups & ad copy',
    color: 'hover:border-indigo-500/40',
    connected: 'border-indigo-500/40 bg-indigo-500/5',
    badge: 'border-indigo-500/20 bg-indigo-500/10 text-indigo-400',
    dot: 'bg-indigo-400',
    docsUrl: 'https://developers.facebook.com/docs/facebook-login/web',
    envKey: 'FACEBOOK_APP_ID',
  },
] as const;

type PlatformId = typeof PLATFORMS[number]['id'];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(iso: string) {
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(iso));
}

function openPopup(url: string): Window | null {
  const w = 520;
  const h = 620;
  const left = window.screenX + (window.innerWidth - w) / 2;
  const top = window.screenY + (window.innerHeight - h) / 2;
  return window.open(url, 'oauth_popup', `width=${w},height=${h},left=${left},top=${top},scrollbars=yes`);
}

// ---------------------------------------------------------------------------
// Connect button — one per platform tile
// ---------------------------------------------------------------------------

function ConnectButton({
  platformId,
  onConnected,
}: {
  platformId: PlatformId;
  onConnected: () => void;
}) {
  const [state, setState] = useState<'idle' | 'loading' | 'popup' | 'error'>('idle');
  const [errorMsg, setErrorMsg] = useState('');
  const [notConfigured, setNotConfigured] = useState(false);
  const [docsUrl, setDocsUrl] = useState('');
  const popupRef = useRef<Window | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const platform = PLATFORMS.find((p) => p.id === platformId)!;

  // Listen for postMessage from popup callback page
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      if (typeof event.data !== 'object' || event.data?.platform !== platformId) return;
      // Clean up
      if (pollRef.current) clearInterval(pollRef.current);
      popupRef.current?.close();
      setState('idle');
      if (event.data.success) {
        onConnected();
      } else {
        setErrorMsg(event.data.message || 'Connection failed.');
        setState('error');
      }
    },
    [platformId, onConnected],
  );

  useEffect(() => {
    window.addEventListener('message', handleMessage);
    return () => {
      window.removeEventListener('message', handleMessage);
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [handleMessage]);

  async function handleConnect() {
    setState('loading');
    setErrorMsg('');
    setNotConfigured(false);

    try {
      const data = await startSocialOAuth(platformId) as any;

      if (!data.configured || !data.auth_url) {
        setNotConfigured(true);
        setDocsUrl(data.setup_url ?? platform.docsUrl);
        setState('idle');
        return;
      }

      const popup = openPopup(data.auth_url);
      if (!popup) {
        setErrorMsg('Popup was blocked. Please allow popups for this site and try again.');
        setState('error');
        return;
      }
      popupRef.current = popup;
      setState('popup');

      // Poll for popup closed without postMessage (user closed manually)
      pollRef.current = setInterval(() => {
        if (popup.closed) {
          if (pollRef.current) clearInterval(pollRef.current);
          setState((current) => (current === 'popup' ? 'idle' : current));
        }
      }, 800);
    } catch {
      setErrorMsg('Failed to start connection. Please try again.');
      setState('error');
    }
  }

  if (notConfigured) {
    return (
      <div className="flex flex-col gap-2">
        <div className="flex items-start gap-2 rounded-lg border border-apple-blue/20 bg-apple-blue/5 px-3 py-2.5 text-xs">
          <Settings size={12} className="mt-0.5 flex-shrink-0 text-apple-blue" />
          <span className="text-ink-soft">
            API credentials not configured.{' '}
            <a href={docsUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-0.5 text-apple-blue hover:underline">
              Setup guide <ExternalLink size={10} />
            </a>
          </span>
        </div>
        <p className="text-[10px] text-ink-faint">
          Add <code className="rounded bg-white/[0.05] px-1">{platform.envKey}</code> to your <code className="rounded bg-white/[0.05] px-1">.env</code>
        </p>
      </div>
    );
  }

  if (state === 'error') {
    return (
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/5 px-3 py-2 text-xs text-red-400">
          <AlertCircle size={12} className="flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
        <Button size="sm" variant="outline" className="w-full text-[12px]" onClick={() => setState('idle')}>
          Try Again
        </Button>
      </div>
    );
  }

  if (state === 'popup') {
    return (
      <Button size="sm" className="w-full text-[12px]" disabled>
        <Loader2 size={12} className="mr-1.5 animate-spin" />
        Waiting for authorisation…
      </Button>
    );
  }

  return (
    <Button
      size="sm"
      variant="outline"
      className={cn('w-full text-[12px] transition', platform.color)}
      onClick={() => void handleConnect()}
      disabled={state === 'loading'}
    >
      {state === 'loading'
        ? <><Loader2 size={12} className="mr-1.5 animate-spin" /> Connecting…</>
        : <>Connect {platform.label}</>}
    </Button>
  );
}

// ---------------------------------------------------------------------------
// Platform tile
// ---------------------------------------------------------------------------

function PlatformTile({
  platform,
  connectedAccounts,
  onConnected,
  onDisconnect,
}: {
  platform: typeof PLATFORMS[number];
  connectedAccounts: SocialAccount[];
  onConnected: () => void;
  onDisconnect: (id: number) => void;
}) {
  const isConnected = connectedAccounts.length > 0;
  const [removing, setRemoving] = useState<number | null>(null);

  async function handleDisconnect(id: number) {
    setRemoving(id);
    try {
      await removeSocialAccount(id);
      onDisconnect(id);
    } finally {
      setRemoving(null);
    }
  }

  return (
    <div
      className={cn(
        'group flex flex-col gap-4 rounded-xl border p-5 transition-all duration-200',
        isConnected ? platform.connected : 'border-white/[0.06] bg-surface-2 hover:border-white/[0.12]',
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              'flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl border',
              isConnected ? platform.badge : 'border-white/[0.08] bg-white/[0.04] text-ink-faint',
            )}
          >
            {platform.icon}
          </div>
          <div>
            <p className="font-semibold text-ink">{platform.label}</p>
            <p className="text-xs text-ink-soft">{platform.description}</p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 flex-shrink-0">
          {isConnected ? (
            <span className="flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-[11px] font-semibold text-emerald-400">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Connected
            </span>
          ) : (
            <span className="rounded-full border border-white/[0.08] bg-white/[0.04] px-2.5 py-1 text-[11px] text-ink-faint">
              Not connected
            </span>
          )}
        </div>
      </div>

      {/* Connected accounts list */}
      {connectedAccounts.map((account) => (
        <div
          key={account.id}
          className="flex items-center justify-between gap-3 rounded-lg border border-white/[0.06] bg-white/[0.03] px-3 py-2.5"
        >
          <div className="flex items-center gap-2.5 min-w-0">
            {account.profile_image_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={account.profile_image_url} alt="" className="h-7 w-7 rounded-full object-cover" />
            ) : (
              <div className={cn('flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full border text-[11px] font-bold', platform.badge)}>
                {account.account_name[0]?.toUpperCase()}
              </div>
            )}
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-ink">{account.account_name}</p>
              <p className="text-[10px] text-ink-faint">Connected {formatDate(account.created_at)}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => void handleDisconnect(account.id)}
            disabled={removing === account.id}
            title="Disconnect"
            className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-md border border-white/[0.06] bg-white/[0.03] text-ink-faint opacity-0 transition group-hover:opacity-100 hover:border-red-500/30 hover:bg-red-500/10 hover:text-red-400"
          >
            {removing === account.id
              ? <Loader2 size={13} className="animate-spin" />
              : <Trash2 size={13} />}
          </button>
        </div>
      ))}

      {/* Connect button */}
      <ConnectButton platformId={platform.id} onConnected={onConnected} />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function SocialAccountsPage() {
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadAccounts() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchSocialAccounts();
      setAccounts(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load accounts');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void loadAccounts(); }, []);

  function handleDisconnect(id: number) {
    setAccounts((prev) => prev.filter((a) => a.id !== id));
  }

  const totalConnected = PLATFORMS.filter((p) =>
    accounts.some((a) => a.platform === p.id),
  ).length;

  return (
    <div className="flex flex-col gap-6 p-4 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          eyebrow="Automation"
          title="Social Accounts"
          description="Connect your social media accounts to publish content directly from the platform"
        >
          <div className="flex items-center gap-2 text-xs text-ink-soft">
            <span className="flex items-center gap-1.5 rounded-full border border-white/[0.08] bg-white/[0.04] px-3 py-1">
              <CheckCircle2 size={12} className="text-emerald-400" />
              {totalConnected} of {PLATFORMS.length} connected
            </span>
          </div>
        </PageHeader>

        <Button variant="outline" size="sm" onClick={() => void loadAccounts()} disabled={loading} className="flex-shrink-0">
          <RefreshCw size={13} className={cn('mr-1.5', loading && 'animate-spin')} />
          Refresh
        </Button>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          <AlertCircle size={14} className="flex-shrink-0" />
          {error}
        </div>
      )}

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {PLATFORMS.map((p) => (
            <div key={p.id} className="h-40 animate-pulse rounded-xl border border-white/[0.06] bg-surface-2" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {PLATFORMS.map((platform) => (
            <PlatformTile
              key={platform.id}
              platform={platform}
              connectedAccounts={accounts.filter((a) => a.platform === platform.id)}
              onConnected={loadAccounts}
              onDisconnect={handleDisconnect}
            />
          ))}
        </div>
      )}

      {/* How it works */}
      <Card className="p-5">
        <h2 className="mb-4 text-sm font-semibold text-ink">How the OAuth connection works</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          {[
            {
              step: '1',
              title: 'Click Connect',
              desc: 'A secure popup opens and redirects you to the platform\'s official login page.',
            },
            {
              step: '2',
              title: 'Authorise access',
              desc: 'You approve the permissions on the platform. No passwords are ever stored here.',
            },
            {
              step: '3',
              title: 'Publish directly',
              desc: 'Use the Trending Post or Campaign flows to schedule and post content to connected accounts.',
            },
          ].map(({ step, title, desc }) => (
            <div key={step} className="flex gap-3">
              <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-apple-blue/15 text-[11px] font-bold text-apple-blue">
                {step}
              </div>
              <div>
                <p className="text-sm font-semibold text-ink">{title}</p>
                <p className="mt-0.5 text-xs text-ink-soft">{desc}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 flex items-start gap-2 rounded-lg border border-apple-blue/20 bg-apple-blue/5 px-3 py-2.5 text-xs text-ink-soft">
          <Settings size={12} className="mt-0.5 flex-shrink-0 text-apple-blue" />
          <span>
            <strong className="text-apple-blue">For developers:</strong> Add your OAuth app credentials to <code className="rounded bg-white/[0.05] px-1">.env</code> —
            {' '}<code className="rounded bg-white/[0.05] px-1">LINKEDIN_CLIENT_ID</code>,
            {' '}<code className="rounded bg-white/[0.05] px-1">TWITTER_CLIENT_ID</code>,
            {' '}<code className="rounded bg-white/[0.05] px-1">FACEBOOK_APP_ID</code>,
            {' '}<code className="rounded bg-white/[0.05] px-1">GOOGLE_CLIENT_ID</code>.
            {' '}Each platform\'s developer portal link is shown when credentials are missing.
          </span>
        </div>
      </Card>

      {accounts.length === 0 && !loading && (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-white/[0.06] bg-surface-2 py-12 text-center">
          <WifiOff size={32} className="text-ink-faint" />
          <p className="text-sm font-medium text-ink-soft">No accounts connected yet</p>
          <p className="text-xs text-ink-faint">Click any platform tile above to connect via OAuth.</p>
        </div>
      )}
    </div>
  );
}
