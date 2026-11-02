import { useState, useMemo, useCallback } from 'react';
import {
  ArrowUpDown, ArrowUp, ArrowDown, Zap, Search, X, Sliders,
} from 'lucide-react';
import { useData } from '@/context/useData';
import { EmptyState } from '@/components/EmptyState';
import { Panel, PanelHeader } from '@/components/Panel';
import { DEFAULT_WEIGHTS, runAnalysis } from '@/data/analysis';
import type { FeatureRow, ScoringWeights } from '@/data/types';

type SortKey = keyof Pick<FeatureRow, 'name' | 'customerDemand' | 'businessValue' | 'urgency' | 'strategicAlignment' | 'devEffort' | 'wsjfScore' | 'priorityRank'>;
type SortDir = 'asc' | 'desc';

export function FeaturesPage() {
  const { analysisResult, analysisDataset } = useData();
  const [sortKey, setSortKey] = useState<SortKey>('priorityRank');
  const [sortDir, setSortDir] = useState<SortDir>('asc');
  const [search, setSearch] = useState('');
  const [priorityFilter, setPriorityFilter] = useState<'all' | 'Critical' | 'High' | 'Medium' | 'Low'>('all');
  const [showWeights, setShowWeights] = useState(false);
  const [weights, setWeights] = useState<ScoringWeights>(DEFAULT_WEIGHTS);
  const [selectedFeature, setSelectedFeature] = useState<FeatureRow | null>(null);

  const recomputedFeatures = useMemo(() => {
    if (!analysisDataset) return [];
    const result = runAnalysis(analysisDataset, weights);
    return result.features;
  }, [analysisDataset, weights]);

  const sortedFeatures = useMemo(() => {
    const features = [...recomputedFeatures];
    features.sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      const cmp = typeof aVal === 'string' ? aVal.localeCompare(String(bVal)) : (aVal as number) - (bVal as number);
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return features;
  }, [recomputedFeatures, sortKey, sortDir]);

  const filteredFeatures = useMemo(() => {
    return sortedFeatures.filter((f) => {
      if (priorityFilter !== 'all' && f.priorityLabel !== priorityFilter) return false;
      if (search && !f.name.toLowerCase().includes(search.toLowerCase()) && !f.id.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [sortedFeatures, priorityFilter, search]);

  const toggleSort = useCallback((key: SortKey) => {
    setSortKey((prev) => {
      if (prev === key) {
        setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
        return prev;
      }
      setSortDir(key === 'name' ? 'asc' : 'desc');
      return key;
    });
  }, []);

  const updateWeight = useCallback((key: keyof ScoringWeights, value: number) => {
    setWeights((w) => ({ ...w, [key]: value }));
  }, []);

  if (!analysisResult || !analysisDataset) {
    return <div className="p-6"><EmptyState title="No data" message="Run an analysis to see features." icon={<Zap className="w-6 h-6 text-slate-400" />} /></div>;
  }

  if (analysisResult.features.length === 0) {
    return (
      <div className="p-6">
        <EmptyState
          title="Feature prioritization unavailable"
          message="This analysis requires customer demand, business value, and development effort columns. Map these fields in the Data Workspace."
          requiredFields={['Customer Demand', 'Business Value', 'Dev Effort']}
          icon={<Zap className="w-6 h-6 text-slate-400" />}
        />
      </div>
    );
  }

  const columns: { key: SortKey; label: string; align: 'left' | 'right' }[] = [
    { key: 'priorityRank', label: 'Rank', align: 'right' },
    { key: 'name', label: 'Feature', align: 'left' },
    { key: 'wsjfScore', label: 'WSJF', align: 'right' },
    { key: 'customerDemand', label: 'Demand', align: 'right' },
    { key: 'businessValue', label: 'Value', align: 'right' },
    { key: 'urgency', label: 'Urgency', align: 'right' },
    { key: 'strategicAlignment', label: 'Strategic', align: 'right' },
    { key: 'devEffort', label: 'Effort', align: 'right' },
  ];

  return (
    <div className="p-5 space-y-4 animate-fade-in">
      {/* Scoring explanation + weights toggle */}
      <Panel>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-navy-50 flex items-center justify-center shrink-0">
              <Zap className="w-4 h-4 text-navy-600" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-navy-700">Weighted Shortest Job First (WSJF)</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Score = (Value×w + Urgency×w + Strategic×w) × (1 + Demand×w) / (Effort×w). Adjust weights to re-rank features in real time.
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowWeights((v) => !v)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-navy-600 bg-navy-50 border border-navy-100 rounded-lg hover:bg-navy-100 transition-colors shrink-0"
          >
            <Sliders className="w-3.5 h-3.5" />
            {showWeights ? 'Hide' : 'Scoring'} Weights
          </button>
        </div>

        {showWeights && (
          <div className="mt-4 pt-4 border-t border-slate-100 grid grid-cols-2 md:grid-cols-5 gap-3 animate-fade-in">
            {(Object.keys(weights) as (keyof ScoringWeights)[]).map((key) => (
              <div key={key}>
                <label className="text-[11px] font-medium text-slate-500 capitalize block mb-1">
                  {key.replace(/([A-Z])/g, ' $1').trim()}
                </label>
                <input
                  type="range"
                  min={0}
                  max={2}
                  step={0.1}
                  value={weights[key]}
                  onChange={(e) => updateWeight(key, Number(e.target.value))}
                  className="w-full accent-teal-500"
                />
                <span className="text-xs font-semibold text-navy-600">{weights[key].toFixed(1)}</span>
              </div>
            ))}
            <button
              onClick={() => setWeights(DEFAULT_WEIGHTS)}
              className="self-end text-xs text-slate-500 hover:text-navy-600 transition-colors"
            >
              Reset
            </button>
          </div>
        )}
      </Panel>

      {/* Filters + table */}
      <Panel>
        <div className="flex items-center gap-3 mb-3 flex-wrap">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search features by name or ID…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-400/30 focus:border-teal-400"
            />
          </div>
          <div className="flex items-center gap-1.5">
            {(['all', 'Critical', 'High', 'Medium', 'Low'] as const).map((p) => (
              <button
                key={p}
                onClick={() => setPriorityFilter(p)}
                className={`px-2.5 py-1.5 text-xs font-medium rounded-md transition-colors ${
                  priorityFilter === p
                    ? 'bg-navy-600 text-white'
                    : 'bg-slate-50 text-slate-600 border border-slate-200 hover:bg-slate-100'
                }`}
              >
                {p === 'all' ? 'All' : p}
              </button>
            ))}
          </div>
          <span className="text-xs text-slate-400">{filteredFeatures.length} of {recomputedFeatures.length}</span>
        </div>

        <div className="overflow-x-auto scrollbar-thin">
          <table className="w-full text-sm">
            <thead className="bg-slate-50/60 border-b border-slate-200">
              <tr>
                <th className="text-left py-2.5 px-3 font-medium text-slate-500 text-[11px] uppercase tracking-wide">Priority</th>
                {columns.map((col) => (
                  <th
                    key={col.key}
                    className={`py-2.5 px-3 font-medium text-slate-500 text-[11px] uppercase tracking-wide cursor-pointer select-none hover:text-navy-600 transition-colors ${col.align === 'right' ? 'text-right' : 'text-left'}`}
                    onClick={() => toggleSort(col.key)}
                  >
                    <span className={`inline-flex items-center gap-1 ${col.align === 'right' ? 'flex-row-reverse' : ''}`}>
                      {col.label}
                      {sortKey === col.key ? (
                        sortDir === 'asc' ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />
                      ) : (
                        <ArrowUpDown className="w-3 h-3 opacity-30" />
                      )}
                    </span>
                  </th>
                ))}
                <th className="text-left py-2.5 px-3 font-medium text-slate-500 text-[11px] uppercase tracking-wide">Release</th>
                <th className="py-2.5 px-3"></th>
              </tr>
            </thead>
            <tbody>
              {filteredFeatures.map((f) => (
                <tr
                  key={f.id}
                  onClick={() => setSelectedFeature(f)}
                  className="border-b border-slate-100 hover:bg-slate-50/40 transition-colors cursor-pointer"
                >
                  <td className="py-2.5 px-3"><PriorityBadge label={f.priorityLabel} /></td>
                  <td className="py-2.5 px-3 text-right font-semibold text-navy-700">#{f.priorityRank}</td>
                  <td className="py-2.5 px-3 text-slate-700 font-medium">{f.name}</td>
                  <td className="py-2.5 px-3 text-right font-bold text-teal-600">{f.wsjfScore.toFixed(2)}</td>
                  <td className="py-2.5 px-3 text-right text-slate-600">{f.customerDemand}</td>
                  <td className="py-2.5 px-3 text-right text-slate-600">{f.businessValue.toFixed(1)}</td>
                  <td className="py-2.5 px-3 text-right text-slate-600">{f.urgency}</td>
                  <td className="py-2.5 px-3 text-right text-slate-600">{f.strategicAlignment}</td>
                  <td className="py-2.5 px-3 text-right text-slate-600">{f.devEffort}</td>
                  <td className="py-2.5 px-3 text-slate-500 text-xs">{f.releaseId ?? '—'}</td>
                  <td className="py-2.5 px-3 text-right">
                    <span className="text-[10px] text-teal-500 font-medium opacity-0 group-hover:opacity-100">View</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredFeatures.length === 0 && (
          <div className="py-8 text-center text-sm text-slate-400">No features match the current filters.</div>
        )}
      </Panel>

      {/* Feature detail drawer */}
      {selectedFeature && (
        <FeatureDrawer feature={selectedFeature} onClose={() => setSelectedFeature(null)} />
      )}
    </div>
  );
}

function FeatureDrawer({ feature, onClose }: { feature: FeatureRow; onClose: () => void }) {
  const metrics = [
    { label: 'WSJF Score', value: feature.wsjfScore.toFixed(2), accent: true },
    { label: 'Customer Demand', value: String(feature.customerDemand) },
    { label: 'Business Value', value: feature.businessValue.toFixed(1) },
    { label: 'Urgency', value: String(feature.urgency) },
    { label: 'Strategic Alignment', value: String(feature.strategicAlignment) },
    { label: 'Dev Effort', value: String(feature.devEffort) },
  ];

  return (
    <>
      <div className="fixed inset-0 bg-black/30 z-30" onClick={onClose} />
      <div className="fixed right-0 top-0 h-full w-[400px] bg-white shadow-xl z-40 animate-slide-in-right overflow-y-auto scrollbar-thin">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200">
          <div>
            <p className="text-[10px] text-slate-400 font-medium uppercase tracking-wide">Feature Detail</p>
            <h3 className="text-base font-semibold text-navy-800 mt-0.5">{feature.name}</h3>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-5 space-y-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-navy-50 text-navy-600 font-bold flex items-center justify-center text-sm">
              #{feature.priorityRank}
            </div>
            <PriorityBadge label={feature.priorityLabel} />
            {feature.releaseId && (
              <span className="px-2 py-0.5 text-xs bg-slate-100 text-slate-600 rounded-md border border-slate-200">{feature.releaseId}</span>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            {metrics.map((m) => (
              <div key={m.label} className={`rounded-lg p-3 border ${m.accent ? 'bg-teal-50 border-teal-200' : 'bg-slate-50 border-slate-200'}`}>
                <p className={`text-lg font-bold leading-tight ${m.accent ? 'text-teal-600' : 'text-navy-700'}`}>{m.value}</p>
                <p className="text-[11px] text-slate-500 mt-0.5">{m.label}</p>
              </div>
            ))}
          </div>

          <div>
            <h4 className="text-xs font-semibold text-navy-700 mb-2">Scoring Breakdown</h4>
            <div className="bg-slate-50 rounded-lg p-3 text-xs text-slate-600 space-y-1.5">
              <p>Value component: {((feature.businessValue + feature.urgency + feature.strategicAlignment)).toFixed(1)}</p>
              <p>Demand multiplier: ×{(1 + feature.customerDemand * 0.1).toFixed(2)}</p>
              <p>Effort divisor: ÷{feature.devEffort}</p>
              <div className="border-t border-slate-200 pt-1.5 mt-1.5">
                <p className="font-semibold text-navy-700">Result: {feature.wsjfScore.toFixed(2)}</p>
              </div>
            </div>
          </div>

          <div>
            <h4 className="text-xs font-semibold text-navy-700 mb-2">Metadata</h4>
            <div className="space-y-1.5 text-xs">
              <Row label="Feature ID" value={feature.id} />
              {feature.taskId && <Row label="Linked Task" value={feature.taskId} />}
              <Row label="Release" value={feature.releaseId ?? 'Unassigned'} />
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-slate-400">{label}</span>
      <span className="font-medium text-slate-700">{value}</span>
    </div>
  );
}

function PriorityBadge({ label }: { label: 'Critical' | 'High' | 'Medium' | 'Low' }) {
  const styles = {
    Critical: 'bg-red-100 text-red-700 border-red-200',
    High: 'bg-orange-100 text-orange-700 border-orange-200',
    Medium: 'bg-amber-100 text-amber-700 border-amber-200',
    Low: 'bg-lime-100 text-lime-700 border-lime-200',
  };
  return <span className={`inline-block px-2 py-0.5 text-[10px] font-medium rounded border ${styles[label]}`}>{label}</span>;
}
