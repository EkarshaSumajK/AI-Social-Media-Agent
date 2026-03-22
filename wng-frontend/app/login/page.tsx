'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight, Loader2 } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { login } from '@/lib/api';
import { setSession } from '@/lib/auth';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload = await login(email, password);
      setSession(payload.user, payload.access_token);
      router.replace('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="relative flex min-h-screen w-full items-center justify-center overflow-hidden px-6 py-12" style={{ background: 'var(--app-bg)', transition: 'background 0.2s ease' }}>
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage: `
            linear-gradient(var(--glass-border) 1px, transparent 1px),
            linear-gradient(90deg, var(--glass-border) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
        }}
      />

      <div
        className="pointer-events-none absolute"
        style={{
          width: 600,
          height: 600,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(240,165,0,0.06) 0%, transparent 70%)',
          top: '-10%',
          left: '-10%',
        }}
      />
      <div
        className="pointer-events-none absolute"
        style={{
          width: 400,
          height: 400,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(59,130,246,0.06) 0%, transparent 70%)',
          bottom: '-5%',
          right: '10%',
        }}
      />

      <Card className="relative w-full max-w-[420px] animate-fade-up overflow-hidden border-white/[0.08] shadow-[0_40px_80px_rgba(0,0,0,0.3)]">
        <div className="h-0.5 bg-gradient-to-r from-apple-blue via-apple-blue/40 to-transparent" />

        <CardHeader className="space-y-0 px-8 pb-4 pt-8">
          <div className="mb-6 flex flex-wrap items-center gap-2">
            {[
              { label: 'Horizon', color: 'bg-cyan-400' },
              { label: 'Connect', color: 'bg-violet-400' },
              { label: 'Parentshala', color: 'bg-pink-400' },
            ].map((platform) => (
              <Badge key={platform.label} variant="secondary" className="gap-1.5 border-white/[0.08] py-1 text-[10px] font-medium text-ink-soft">
                <span className={`h-1.5 w-1.5 rounded-full ${platform.color}`} />
                {platform.label}
              </Badge>
            ))}
          </div>

          <CardTitle className="text-3xl leading-tight">
            Wellnest Intelligent
            <br />
            <span className="text-apple-blue">Marketing</span>
          </CardTitle>
          <CardDescription className="mt-2 text-sm text-ink-faint">Sign in to access your content ops workspace.</CardDescription>
        </CardHeader>

        <CardContent className="px-8 pb-8">
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="space-y-1.5">
              <Label htmlFor="email">Email address</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@company.com"
                required
                autoComplete="email"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="••••••••"
                required
                autoComplete="current-password"
              />
            </div>

            {error && (
              <div className="rounded-md border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-400">
                {error}
              </div>
            )}

            <Button className="mt-2 w-full justify-between" type="submit" disabled={loading}>
              <span>{loading ? 'Signing in...' : 'Sign in'}</span>
              {loading ? <Loader2 size={15} className="animate-spin" /> : <ArrowRight size={15} />}
            </Button>
          </form>
        </CardContent>
      </Card>

      <p className="absolute bottom-6 left-0 right-0 text-center text-[11px] text-ink-faint">
        Wellnest Intelligent Marketing (WIM) - Secure Access
      </p>
    </main>
  );
}
