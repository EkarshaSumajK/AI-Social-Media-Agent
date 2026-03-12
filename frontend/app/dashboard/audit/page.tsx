'use client';

import { Loader2 } from 'lucide-react';
import { useEffect, useState } from 'react';

import { PageHeader } from '@/components/page-header';
import { fetchAudit } from '@/lib/api';
import type { AuditLog } from '@/lib/types';

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchAudit(100);
        setLogs(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load audit log');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  function formatEntityInfo(log: AuditLog) {
    const skip = ['id', 'action', 'created_at'];
    const parts: string[] = [];
    const rec = log as Record<string, unknown>;
    if (rec.entity_type) parts.push(`Type: ${rec.entity_type}`);
    if (rec.entity_id) parts.push(`ID: ${rec.entity_id}`);
    if (rec.actor_id != null) parts.push(`Actor: ${rec.actor_id}`);
    if (rec.details && typeof rec.details === 'object' && !Array.isArray(rec.details)) {
      const d = rec.details as Record<string, unknown>;
      const extra = Object.entries(d)
        .filter(([k]) => !skip.includes(k))
        .map(([k, v]) => `${k}: ${String(v)}`);
      parts.push(...extra);
    }
    return parts.length ? parts.join(' · ') : null;
  }

  return (
    <div className="flex flex-col gap-6 p-4 sm:p-6">
      <PageHeader
        title="Audit Log"
        description="Track all system activities"
      />

      {error && (
        <div className="rounded-xl border border-ember/30 bg-ember/5 px-4 py-3 text-sm text-ember">
          {error}
        </div>
      )}

      <section className="rounded-lg border bg-card text-card-foreground shadow-sm p-5">
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-ink-soft">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading audit log...
          </div>
        ) : logs.length === 0 ? (
          <p className="text-sm text-ink-soft">No audit records yet.</p>
        ) : (
          <div className="relative">
            <div className="absolute left-[7px] top-2 bottom-2 w-0.5 bg-slate-200" />
            <ul className="space-y-0">
              {logs.map((log) => {
                const entityInfo = formatEntityInfo(log);
                return (
                  <li key={log.id} className="relative flex gap-4 pb-6 last:pb-0">
                    <div className="relative z-10 flex h-4 w-4 flex-shrink-0 items-center justify-center rounded-full bg-ocean/20">
                      <div className="h-2 w-2 rounded-full bg-ocean" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-ink">{log.action}</p>
                      {entityInfo && (
                        <p className="mt-0.5 text-xs text-ink-soft">{entityInfo}</p>
                      )}
                      <p className="mt-1 text-[10px] text-ink-soft">
                        {new Date(log.created_at).toLocaleString()}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        )}
      </section>
    </div>
  );
}
