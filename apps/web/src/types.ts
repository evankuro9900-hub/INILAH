export interface League {
  id: string;
  name: string;
  country: string;
  tier: string;
}

export interface Pick {
  id: number;
  fixture_id: number;
  market: string;
  selection: string;
  odds_at_pick: number;
  odds_at_close: number | null;
  estimated_rp: number;
  edge_pct: number; // 0.087 = 8.7%
  stake_pct: number; // 0.015 = 1.5%
  scoring_card: ScoringCard | null;
  reasoning: { reasons?: string[]; candidates?: Candidate[] } | null;
  tags: string[] | null;
  result: 'win' | 'loss' | 'push' | 'void' | null;
  profit_pct: number | null;
  clv_pct: number | null;
  skill_version: string;
  created_at: string;
  validated_at: string | null;
}

export interface ScoringCard {
  form: number;
  xg_xga: number;
  motivation: number;
  home_away: number;
  condition: number;
  h2h: number;
  fatigue: number;
  weather_ref: number;
  weighted_total: number;
  adjustment_pct: number;
  tags: string[];
  notes: string[];
}

export interface Candidate {
  market: string;
  selection: string;
  odds: number;
  implied_prob: number;
  estimated_rp: number;
  edge_pct: number;
}

export interface Fixture {
  id: number;
  external_id: string | null;
  league_id: string;
  home_team: string;
  away_team: string;
  kickoff_utc: string;
  kickoff_wib_date: string;
  status: 'scheduled' | 'live' | 'finished' | 'postponed' | 'canceled';
  home_score: number | null;
  away_score: number | null;
  venue: string | null;
  picks: Pick[];
}

export interface FetchStatus {
  target_date: string;
  cached: boolean;
  cache_fresh: boolean;
  last_fetched_at: string | null;
  fixtures_count: number | null;
  status: 'cached_fresh' | 'cached_stale' | 'pending' | 'failed' | 'missing';
  error: string | null;
}

export interface FixturesResponse {
  target_date: string;
  fetch_status: FetchStatus;
  fixtures: Fixture[];
  counts: Record<string, number>;
}

export interface StatsResponse {
  total_picks: number;
  wins: number;
  losses: number;
  pushes: number;
  pending: number;
  hit_rate: number | null;
  roi_pct: number | null;
  avg_clv_pct: number | null;
  by_market: Record<string, { total: number; wins: number; losses: number; pnl: number }>;
  by_league: Record<string, { total: number; wins: number; losses: number; pnl: number }>;
}
