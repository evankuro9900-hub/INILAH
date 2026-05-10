import { id as idLocale } from 'date-fns/locale';
import { formatInTimeZone } from 'date-fns-tz';

export const WIB_TZ = 'Asia/Jakarta';

export function formatWibDate(dateStr: string): string {
  const d = new Date(`${dateStr}T00:00:00+07:00`);
  return formatInTimeZone(d, WIB_TZ, "EEEE, dd MMM yyyy", { locale: idLocale });
}

export function formatWibTime(utcIso: string): string {
  const d = new Date(utcIso);
  return formatInTimeZone(d, WIB_TZ, 'HH:mm');
}

export function formatRelative(utcIso: string): string {
  const d = new Date(utcIso);
  const diffMs = Date.now() - d.getTime();
  const diffMin = Math.round(diffMs / 60000);
  if (diffMin < 1) return 'baru saja';
  if (diffMin < 60) return `${diffMin}m lalu`;
  const diffH = Math.floor(diffMin / 60);
  const remMin = diffMin % 60;
  if (diffH < 24) return remMin > 0 ? `${diffH}j ${remMin}m lalu` : `${diffH}j lalu`;
  const diffD = Math.floor(diffH / 24);
  return `${diffD}h lalu`;
}

export function todayWibIso(): string {
  return formatInTimeZone(new Date(), WIB_TZ, 'yyyy-MM-dd');
}

export function addDays(isoDate: string, days: number): string {
  const d = new Date(`${isoDate}T00:00:00+07:00`);
  d.setUTCDate(d.getUTCDate() + days);
  return formatInTimeZone(d, WIB_TZ, 'yyyy-MM-dd');
}

export function pct(value: number, digits = 1): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${(value * 100).toFixed(digits)}%`;
}

export function pctRaw(value: number, digits = 1): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(digits)}%`;
}

export function tierLabel(tier: string): string {
  const map: Record<string, string> = {
    T1: 'Tier 1',
    T2: 'Tier 2',
    T3: 'Tier 3',
    'T-OCEANIA': 'Oceania',
  };
  return map[tier] ?? tier;
}
