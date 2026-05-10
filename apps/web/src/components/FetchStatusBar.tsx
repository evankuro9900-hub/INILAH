import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api';
import type { FetchStatus } from '../types';
import { formatRelative } from '../utils/format';

interface Props {
  date: string;
  status: FetchStatus;
}

export function FetchStatusBar({ date, status }: Props) {
  const qc = useQueryClient();
  const [busy, setBusy] = useState(false);

  const force = useMutation({
    mutationFn: () => api.forceFetch(date),
    onMutate: () => setBusy(true),
    onSettled: () => {
      setBusy(false);
      qc.invalidateQueries({ queryKey: ['fixtures', date] });
    },
  });

  const colors: Record<string, string> = {
    cached_fresh: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
    cached_stale: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    pending: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
    failed: 'bg-red-500/15 text-red-300 border-red-500/30',
    missing: 'bg-slate-700 text-slate-300 border-slate-600',
  };

  const labels: Record<string, string> = {
    cached_fresh: '🟢 Cached fresh',
    cached_stale: '🟠 Cached (akan refresh)',
    pending: '🟡 Fetching...',
    failed: '🔴 Failed',
    missing: '⚫ Belum di-fetch',
  };

  const colorCls = colors[status.status] ?? colors.missing;
  const label = labels[status.status] ?? '?';

  return (
    <div className={`card border ${colorCls} flex items-center justify-between gap-3 flex-wrap`}>
      <div className="text-sm">
        <span className="font-semibold">{label}</span>
        {status.last_fetched_at && (
          <span className="ml-2 text-slate-300">
            (terakhir fetch {formatRelative(status.last_fetched_at)})
          </span>
        )}
        {status.fixtures_count !== null && (
          <span className="ml-2 text-slate-300">
            · {status.fixtures_count} fixtures
          </span>
        )}
      </div>
      <button
        className="btn-primary"
        disabled={busy || force.isPending}
        onClick={() => force.mutate()}
      >
        {busy ? '⏳ Fetching...' : '🔄 Fetch sekarang'}
      </button>
    </div>
  );
}
