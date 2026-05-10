import { addDays, formatWibDate, todayWibIso } from '../utils/format';

interface Props {
  value: string;
  onChange: (date: string) => void;
}

const RANGE_PAST = 3;
const RANGE_FUTURE = 7;

export function DatePicker({ value, onChange }: Props) {
  const today = todayWibIso();
  const dates: string[] = [];
  for (let d = -RANGE_PAST; d <= RANGE_FUTURE; d++) {
    dates.push(addDays(today, d));
  }

  const isPast = value < today;
  const isToday = value === today;
  const isFuture = value > today;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">
            Tanggal pertandingan (WIB)
          </div>
          <div className="text-lg font-bold flex items-center gap-2">
            <span>{formatWibDate(value)}</span>
            {isToday && (
              <span className="pill bg-emerald-500/15 text-emerald-300">Hari ini</span>
            )}
            {isPast && <span className="pill bg-slate-700 text-slate-300">Past</span>}
            {isFuture && <span className="pill bg-blue-500/15 text-blue-300">Future</span>}
          </div>
        </div>
        <button
          className="btn-secondary"
          onClick={() => onChange(today)}
          disabled={isToday}
        >
          ⏎ Hari ini
        </button>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-3">
        {dates.map((d) => {
          const active = d === value;
          const isT = d === today;
          const offset = Math.round(
            (new Date(`${d}T00:00:00+07:00`).getTime() - new Date(`${today}T00:00:00+07:00`).getTime()) / 86400000,
          );
          let label: string;
          if (offset === 0) label = 'Today';
          else if (offset > 0) label = `H+${offset}`;
          else label = `H${offset}`;
          return (
            <button
              key={d}
              onClick={() => onChange(d)}
              className={`btn text-xs ${
                active
                  ? 'bg-emerald-600 text-white'
                  : isT
                  ? 'bg-slate-800 ring-1 ring-emerald-500/50 text-slate-100'
                  : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
              }`}
            >
              {label}
            </button>
          );
        })}
      </div>

      <input
        type="date"
        value={value}
        min={dates[0]}
        max={dates[dates.length - 1]}
        onChange={(e) => onChange(e.target.value)}
        className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
      />
    </div>
  );
}
