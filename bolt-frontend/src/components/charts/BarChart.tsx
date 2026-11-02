import type { ChartData } from '@/data/types';

interface BarChartProps {
  data: ChartData[];
  height?: number;
  valueFormatter?: (v: number) => string;
}

export function BarChart({ data, height = 220, valueFormatter }: BarChartProps) {
  const maxVal = Math.max(...data.map((d) => d.value), 1);
  const barWidth = 100 / (data.length * 1.5);
  const gap = barWidth * 0.5;

  return (
    <div className="w-full">
      <svg viewBox={`0 0 100 ${height / 2.2}`} className="w-full" style={{ height }} preserveAspectRatio="none">
        {data.map((d, i) => {
          const barHeight = (d.value / maxVal) * (height / 2.5);
          const x = i * (barWidth + gap) + gap;
          const y = height / 2.2 - barHeight - 2;
          return (
            <g key={d.label}>
              <rect
                x={x}
                y={y}
                width={barWidth}
                height={barHeight}
                rx={0.5}
                fill={d.color ?? '#14b8a6'}
                className="transition-all duration-500"
                style={{ opacity: 0.9 }}
              />
            </g>
          );
        })}
      </svg>
      <div className="flex justify-around mt-2">
        {data.map((d) => (
          <div key={d.label} className="text-center">
            <p className="text-xs font-medium text-slate-600 truncate max-w-[80px]">{d.label}</p>
            <p className="text-sm font-semibold text-navy-700">
              {valueFormatter ? valueFormatter(d.value) : d.value}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
