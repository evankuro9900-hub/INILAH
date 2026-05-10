import { useQuery } from '@tanstack/react-query';
import { api } from '../api';
import { pctRaw } from '../utils/format';

export function StatsPanel() {
  const { data, isLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: () => api.stats(),
  });

  if (isLoading) {
    return <div className="card text-slate-400 text-sm">Loading stats...</div>;
  }
  if (!data) return null;

  return (
    <div className="card">
      <div className="text-xs text-slate-400 uppercase tracking-wider mb-2">Stats Keseluruhan</div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Stat label="Total picks" value={String(data.total_picks)} />
        <Stat label="Hit rate" value={data.hit_rate !== null ? `${data.hit_rate}%` : '—'} />
        <Stat
          label="ROI"
          value={data.roi_pct !== null ? pctRaw(data.roi_pct, 2) : '—'}
          color={data.roi_pct !== null ? (data.roi_pct >= 0 ? 'emerald' : 'red') : undefined}
        />
        <Stat label="Avg CLV" value={data.avg_clv_pct !== null ? pctRaw(data.avg_clv_pct, 2) : '—'} />
      </div>
      <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
        <div className="bg-emerald-500/10 rounded p-2">
          <div className="text-slate-400">Wins</div>
          <div className="text-emerald-300 font-bold text-lg">{data.wins}</div>
        </div>
        <div className="bg-red-500/10 rounded p-2">
          <div className="text-slate-400">Losses</div>
          <div className="text-red-300 font-bold text-lg">{data.losses}</div>
        </div>
        <div className="bg-amber-500/10 rounded p-2">
          <div className="text-slate-400">Pushes / Pending</div>
          <div className="text-amber-300 font-bold text-lg">
            {data.pushes} / {data.pending}
          </div>
        </div>
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: 'emerald' | 'red';
}) {
  const cls =
    color === 'emerald' ? 'text-emerald-300' : color === 'red' ? 'text-red-300' : 'text-slate-100';
  return (
    <div>
      <div className="text-xs text-slate-400">{label}</div>
      <div className={`text-2xl font-bold ${cls}`}>{value}</div>
    </div>
  );
}
