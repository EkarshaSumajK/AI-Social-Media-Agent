'use client';

import { useEffect, useRef, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';

import { Card } from '@/components/ui/card';
import { fetchMe } from '@/lib/api';
import { clearSession, getStoredToken, setSession } from '@/lib/auth';

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const isLoginRoute = pathname.startsWith('/login');

  // Always false on first render so SSR and client initial render match.
  // useEffect immediately sets true if a token exists (optimistic path).
  const [ready, setReady] = useState(false);
  const validatedRef = useRef(false);

  useEffect(() => {
    if (validatedRef.current) return;
    validatedRef.current = true;

    // Optimistic: if a token is present, unblock the UI immediately.
    // The session is still validated in the background below.
    const hasToken = !!getStoredToken();
    if (isLoginRoute || hasToken) {
      setReady(true);
    }

    let active = true;

    async function validateSession() {
      try {
        const user = await fetchMe();
        setSession(user);
        if (!active) return;
        if (isLoginRoute) {
          router.replace('/dashboard');
        } else {
          setReady(true);
        }
      } catch {
        clearSession();
        if (!active) return;
        if (!isLoginRoute) {
          router.replace('/login');
        } else {
          setReady(true);
        }
      }
    }

    void validateSession();

    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoginRoute]);

  if (!ready) {
    return (
      <div className="flex h-screen items-center justify-center" style={{ background: 'var(--app-bg)' }}>
        <Card className="flex items-center gap-2 px-4 py-3">
          <Loader2 className="h-4 w-4 animate-spin text-apple-blue" />
          <span className="text-sm text-ink-soft">Validating session...</span>
        </Card>
      </div>
    );
  }

  return <>{children}</>;
}
