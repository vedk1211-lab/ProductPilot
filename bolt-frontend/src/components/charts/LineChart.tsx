import type { TrendPoint } from '@/data/types';

interface LineChartProps {
  data: TrendPoint[];
  height?: number;
  color?: string;
}

export function LineChart({ data, height = 200, color = '#14b8a6' }: LineChartProps) {
  if (data.length === 0) return null;

  const width = 100;
  const h = height / 2.2;
  const padding = { top: 8, right: 4, bottom: 16, left: 4 };
  const innerW = width - padding.left - padding.right;
  const innerH = h - padding.top - padding.bottom;

  const maxVal = Math.max(...data.map((d) => d.value), 1);
  const minVal = 0;
  const range = maxVal - minVal || 1;

  const points = data.map((d, i) => ({
    x: padding.left + (data.length === 1 ? innerW / 2 : (i / (data.length - 1)) * innerW),
    y: padding.top + innerH - ((d.value - minVal) / range) * innerH,
    ...d,
  }));

  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(2)} ${p.y.toFixed(2)}`).join(' ');
  const areaD = `${pathD} L ${points[points.length - 1].x.toFixed(2)} ${(padding.top + innerH).toFixed(2)} L ${points[0].x.toFixed(2)} ${(padding.top + innerH).toFixed(2)} Z`;

  return (
    <div className="w-full">
      <svg viewBox={`0 0 ${width} ${h}`} className="w-full" style={{ height }} preserveAspectRatio="none">
        <defs>
          <linearGradient id="lineGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.2} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <path d={areaD} fill="url(#lineGrad)" />
        <path d={pathD} fill="none" stroke={color} strokeWidth={1.5} vectorEffect="non-scaling-stroke" />
        {points.map((p, i) => (
          <g key={i}>
            <circle cx={p.x} cy={p.y} r={1.5} fill={color} vectorEffect="non-scaling-stroke" />
            <title>{`${p.label}: ${p.value}`}</title>
          </g>
        ))}
      </svg>
      <div className="flex justify-between mt-1 px-1">
        {data.map((d, i) => (
          <p key={i} className="text-[10px] text-slate-400 truncate" style={{ maxWidth: `${100 / data.length }%` }}>
            {d.label}
          </p>
        ))}
      </div>
    </div>
  );
}
