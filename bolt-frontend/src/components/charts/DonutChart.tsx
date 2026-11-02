import type { ChartData } from '@/data/types';

interface DonutChartProps {
  data: ChartData[];
  size?: number;
  thickness?: number;
  centerLabel?: string;
  centerValue?: string;
}

export function DonutChart({ data, size = 180, thickness = 28, centerLabel, centerValue }: DonutChartProps) {
  const total = data.reduce((s, d) => s + d.value, 0);
  const radius = (size - thickness) / 2;
  const circumference = 2 * Math.PI * radius;
  const center = size / 2;

  let offset = 0;
  const segments = data.map((d) => {
    const fraction = total > 0 ? d.value / total : 0;
    const dash = fraction * circumference;
    const segment = {
      ...d,
      dashArray: `${dash} ${circumference - dash}`,
      dashOffset: -offset,
    };
    offset += dash;
    return segment;
  });

  return (
    <div className="flex items-center gap-6 flex-wrap">
      <div className="relative shrink-0" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="#f1f5f9"
            strokeWidth={thickness}
          />
          {total > 0 &&
            segments.map((s) => (
              <circle
                key={s.label}
                cx={center}
                cy={center}
                r={radius}
                fill="none"
                stroke={s.color ?? '#14b8a6'}
                strokeWidth={thickness}
                strokeDasharray={s.dashArray}
                strokeDashoffset={s.dashOffset}
                className="transition-all duration-700"
                strokeLinecap="butt"
              />
            ))}
        </svg>
        {(centerLabel || centerValue) && (
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            {centerValue && <span className="text-2xl font-bold text-navy-800">{centerValue}</span>}
            {centerLabel && <span className="text-xs text-slate-400 mt-0.5">{centerLabel}</span>}
          </div>
        )}
      </div>

      <div className="space-y-2 min-w-0">
        {data.map((d) => (
          <div key={d.label} className="flex items-center gap-2.5">
            <div
              className="w-3 h-3 rounded-sm shrink-0"
              style={{ backgroundColor: d.color ?? '#14b8a6' }}
            />
            <span className="text-sm text-slate-600 truncate">{d.label}</span>
            <span className="text-sm font-semibold text-navy-700 ml-auto pl-2">{d.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
