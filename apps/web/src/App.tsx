import { useEffect, useMemo, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from './api';
import type { Fixture } from './types';
import { DatePicker } from './components/DatePicker';
import { FetchStatusBar } from './components/FetchStatusBar';
import { MatchCard } from './components/MatchCard';
import { StatsPanel } from './components/StatsPanel';
import { DisclaimerModal } from './components/DisclaimerModal';
import { todayWibIso } from './utils/format';

export default function App() {
  const queryClient = useQueryClient();
  const [selectedDate, setSelectedDate] = useState<string>(todayWibIso());

  const leaguesQuery = useQuery({
    queryKey: ['leagues'],
    queryFn: () => api.leagues(),
    staleTime: 600_000,
  });

  const fixturesQuery = useQuery({
    queryKey: ['fixtures', selectedDate],
    queryFn: () => api.fixtures(selectedDate),
    refetchInterval: 60_000,
  });

  // Invalidate stats whenever fixtures berhasil di-fetch (picks baru bisa muncul)
  useEffect(() => {
    if (fixturesQuery.data) {
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    }
  }, [fixturesQuery.data, queryClient]);

  const leagueMap = useMemo(() => {
    const map = new Map<string, string>();
    leaguesQuery.data?.forEach((l) => map.set(l.id, l.name));
    return map;
  }, [leaguesQuery.data]);

  const groupedFixtures = useMemo(() => {
    const groups = new Map<string, Fixture[]>();
    if (!fixturesQuery.data) return groups;
    fixturesQuery.data.fixtures.forEach((fx) => {
      const arr = groups.get(fx.league_id) ?? [];
      arr.push(fx);
      groups.set(fx.league_id, arr);
    });
    return groups;
  }, [fixturesQuery.data]);

  const totalPicks = useMemo(
    () => fixturesQuery.data?.fixtures.reduce((acc, fx) => acc + fx.picks.length, 0) ?? 0,
    [fixturesQuery.data],
  );

  const totalFixtures = fixturesQuery.data?.fixtures.length ?? 0;

  return (
    <>
      <DisclaimerModal />
      <div className="min-h-screen">
        <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur sticky top-0 z-10">
          <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-2xl">⚽</span>
              <div>
                <div className="font-bold text-lg leading-tight">Sports Parlay Analyst</div>
                <div className="text-xs text-slate-400">v3.0 · Edge-Based Analysis</div>
              </div>
            </div>
            <div className="text-xs text-slate-400 hidden sm:block">
              {leaguesQuery.data?.length ?? 0} liga aktif
            </div>
          </div>
        </header>

        <main className="max-w-6xl mx-auto p-4 space-y-4">
          <DatePicker value={selectedDate} onChange={setSelectedDate} />

          {fixturesQuery.data && (
            <FetchStatusBar date={selectedDate} status={fixturesQuery.data.fetch_status} />
          )}

          <StatsPanel />

          <div className="card">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="text-sm text-slate-400">
                  {totalFixtures} pertandingan · {totalPicks} picks
                </div>
              </div>
            </div>

            {fixturesQuery.isLoading && (
              <div className="text-slate-400 text-sm">Loading fixtures...</div>
            )}
            {fixturesQuery.isError && (
              <div className="text-red-400 text-sm">
                Error: {(fixturesQuery.error as Error).message}
              </div>
            )}

            {fixturesQuery.data && totalFixtures === 0 && (
              <div className="text-slate-400 text-sm py-8 text-center">
                Tidak ada pertandingan pada tanggal ini.
              </div>
            )}

            <div className="space-y-4">
              {Array.from(groupedFixtures.entries()).map(([leagueId, fixtures]) => (
                <div key={leagueId}>
                  <div className="text-xs uppercase tracking-wider text-slate-400 mb-2">
                    🏆 {leagueMap.get(leagueId) ?? leagueId} ({fixtures.length})
                  </div>
                  <div className="grid gap-3 md:grid-cols-2">
                    {fixtures.map((fx) => (
                      <MatchCard
                        key={fx.id}
                        fixture={fx}
                        leagueName={leagueMap.get(leagueId)}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <footer className="text-xs text-slate-500 text-center py-6">
            Skill v3.0 · Edge-based betting analysis tool · Bukan layanan judi · Bermainlah bertanggung
            jawab
          </footer>
        </main>
      </div>
    </>
  );
}
