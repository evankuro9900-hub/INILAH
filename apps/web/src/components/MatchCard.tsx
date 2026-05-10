import { useState } from 'react';
import type { Fixture, Pick } from '../types';
import { formatWibTime, pctRaw } from '../utils/format';

interface Props {
  fixture: Fixture;
  leagueName?: string;
}

const RESULT_COLORS: Record<string, string> = {
  win: 'bg-emerald-500/20 text-emerald-300',
  loss: 'bg-red-500/20 text-red-300',
  push: 'bg-amber-500/20 text-amber-300',
  void: 'bg-slate-600 text-slate-200',
};

const STATUS_BADGE: Record<string, { cls: string; label: string }> = {
  scheduled: { cls: 'bg-slate-700 text-slate-200', label: 'Belum mulai' },
  live: { cls: 'bg-red-500/30 text-red-200 animate-pulse', label: '● LIVE' },
  finished: { cls: 'bg-slate-800 text-slate-400', label: 'Selesai' },
  postponed: { cls: 'bg-amber-500/20 text-amber-300', label: 'Postponed' },
  canceled: { cls: 'bg-red-700 text-red-200', label: 'Canceled' },
};

function PickBadge({ pick }: { pick: Pick }) {
  const edge = pick.edge_pct * 100;
  const color =
    pick.result === 'win'
      ? 'border-emerald-500 bg-emerald-500/10'
      : pick.result === 'loss'
      ? 'border-red-500 bg-red-500/10'
      : pick.result === 'push'
      ? 'border-amber-500 bg-amber-500/10'
      : 'border-blue-500 bg-blue-500/10';

  return (
    <div className={`border rounded-lg p-3 ${color}`}>
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="text-xs text-slate-400 mb-0.5">PICK ({pick.market})</div>
          <div className="font-semibold text-sm">{pick.selection}</div>
        </div>
        <div className="text-right">
          <div className="text-xs text-slate-400">Edge</div>
          <div className={`font-bold ${edge >= 5 ? 'text-emerald-400' : 'text-amber-400'}`}>
            {pctRaw(edge, 1)}
          </div>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-2 mt-2 text-xs">
        <div>
          <div className="text-slate-500">Odds</div>
          <div className="font-medium">{pick.odds_at_pick.toFixed(2)}</div>
        </div>
        <div>
          <div className="text-slate-500">Stake</div>
          <div className="font-medium">{(pick.stake_pct * 100).toFixed(2)}%</div>
        </div>
        <div>
          <div className="text-slate-500">Est. RP</div>
          <div className="font-medium">{(pick.estimated_rp * 100).toFixed(0)}%</div>
        </div>
      </div>
      {pick.result && (
        <div className="mt-2 flex items-center gap-2">
          <span className={`badge ${RESULT_COLORS[pick.result]}`}>{pick.result.toUpperCase()}</span>
          {pick.profit_pct !== null && (
            <span className="text-xs text-slate-400">
              P/L: {pctRaw(pick.profit_pct * 100, 2)} bankroll
            </span>
          )}
          {pick.clv_pct !== null && (
            <span className="text-xs text-slate-400">CLV: {pctRaw(pick.clv_pct, 1)}</span>
          )}
        </div>
      )}
      {pick.tags && pick.tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {pick.tags.map((t) => (
            <span
              key={t}
              className={`pill text-[10px] ${
                t === 'MOCK_ODDS'
                  ? 'bg-amber-500/20 text-amber-300'
                  : t === 'LOW_DATA'
                  ? 'bg-orange-500/20 text-orange-300'
                  : 'bg-slate-700 text-slate-300'
              }`}
            >
              {t}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export function MatchCard({ fixture, leagueName }: Props) {
  const [open, setOpen] = useState(false);
  const status = STATUS_BADGE[fixture.status] ?? STATUS_BADGE.scheduled;
  const hasScore = fixture.home_score !== null && fixture.away_score !== null;
  const hasPick = fixture.picks.length > 0;
  const topPick = hasPick ? fixture.picks[0] : null;
  const hasMockOdds = topPick?.tags?.includes('MOCK_ODDS') ?? false;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="font-medium uppercase">{leagueName ?? fixture.league_id}</span>
          <span>·</span>
          <span>{formatWibTime(fixture.kickoff_utc)} WIB</span>
          {fixture.venue && (
            <>
              <span>·</span>
              <span className="truncate max-w-[140px]">{fixture.venue}</span>
            </>
          )}
        </div>
        <span className={`badge ${status.cls}`}>{status.label}</span>
      </div>

      <div className="flex items-center gap-2 mb-3">
        <div className="flex-1 text-base font-semibold">{fixture.home_team}</div>
        <div className="text-xl font-bold text-slate-300 px-2">
          {hasScore ? `${fixture.home_score} - ${fixture.away_score}` : 'vs'}
        </div>
        <div className="flex-1 text-base font-semibold text-right">{fixture.away_team}</div>
      </div>

      {hasPick && topPick && (
        <div className="mt-2">
          <button
            onClick={() => setOpen(!open)}
            className="text-xs text-slate-400 hover:text-slate-200 mb-2"
          >
            {open ? '▼' : '▶'} Detail pick & alasan
          </button>
          <PickBadge pick={topPick} />
          {open && topPick.scoring_card && (
            <div className="mt-3 pt-3 border-t border-slate-800 text-xs text-slate-300 space-y-1">
              {topPick.reasoning?.reasons?.map((r, i) => (
                <div key={i}>• {r}</div>
              ))}
              {topPick.scoring_card.notes?.length > 0 && (
                <div className="mt-2 text-amber-300/80">
                  ⚠ {topPick.scoring_card.notes.join(' · ')}
                </div>
              )}
              {hasMockOdds && (
                <div className="mt-2 p-2 bg-amber-500/10 rounded text-amber-200">
                  ℹ️ Odds yang dipakai = mock estimasi internal. Pick bersifat ILUSTRATIF
                  sampai integrasi real bookmaker odds (v1).
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {!hasPick && (
        <div className="text-xs text-slate-500 italic">
          ⏭ Tidak ada pick (edge &lt; threshold liga)
        </div>
      )}
    </div>
  );
}
