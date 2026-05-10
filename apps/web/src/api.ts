import type { FetchStatus, FixturesResponse, League, Pick, StatsResponse } from './types';

// VITE_API_BASE bisa berisi:
// - '/api' (default, mode dev pakai proxy ke localhost:8000)
// - 'https://<host>/api' (production, full URL ke Fly.io)
const API_BASE = ((import.meta.env.VITE_API_BASE as string | undefined) ?? '/api').replace(/\/$/, '');

function buildUrl(path: string): string {
  // Path biasanya '/api/health'. Strip prefix '/api' lalu append ke API_BASE.
  const normalized = path.startsWith('/api') ? path.slice(4) : path;
  return `${API_BASE}${normalized.startsWith('/') ? normalized : '/' + normalized}`;
}

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(buildUrl(path));
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

async function postJSON<T>(path: string): Promise<T> {
  const res = await fetch(buildUrl(path), { method: 'POST' });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const api = {
  health: () => getJSON<{ status: string; leagues_active: number }>('/api/health'),
  leagues: () => getJSON<League[]>('/api/leagues'),
  fixtures: (date: string) => getJSON<FixturesResponse>(`/api/fixtures?date=${date}`),
  fetchStatus: (date: string) => getJSON<FetchStatus>(`/api/fetch_status?date=${date}`),
  forceFetch: (date: string) => postJSON<FetchStatus>(`/api/fetch?date=${date}`),
  picks: (params: { date_from?: string; date_to?: string; league?: string; result?: string; limit?: number } = {}) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => v !== undefined && q.set(k, String(v)));
    return getJSON<Pick[]>(`/api/picks?${q.toString()}`);
  },
  stats: (params: { date_from?: string; date_to?: string; league?: string } = {}) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => v !== undefined && q.set(k, String(v)));
    return getJSON<StatsResponse>(`/api/stats?${q.toString()}`);
  },
};
