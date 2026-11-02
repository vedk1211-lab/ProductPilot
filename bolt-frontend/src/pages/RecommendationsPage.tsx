import {
  Lightbulb, AlertTriangle, Info, AlertCircle, CheckCircle2,
} from 'lucide-react';
import { useData } from '@/context/useData';
import { EmptyState } from '@/components/EmptyState';
import { Panel, PanelHeader } from '@/components/Panel';
import type { Recommendation } from '@/data/types';

export function RecommendationsPage() {
  const { analysisResult, lastAnalysisSummary, analysisMode } = useData();

  if (!analysisResult) {
    return <div className="p-6"><EmptyState title="No data" message="Run an analysis to see recommendations." icon={<Lightbulb className="w-6 h-6 text-slate-400" />} /></div>;
  }

  const { recommendations } = analysisResult;

  const critical = recommendations.filter((r) => r.severity === 'critical');
  const warnings = recommendations.filter((r) => r.severity === 'warning');
  const info = recommendations.filter((r) => r.severity === 'info');

  return (
    <div className="p-5 space-y-4 animate-fade-in">
      {/* Analysis summary */}
      {lastAnalysisSummary && (
        <Panel>
          <PanelHeader
            title="Last Analysis Summary"
            subtitle={`${lastAnalysisSummary.processedRows} rows processed · ${lastAnalysisSummary.skippedRows} skipped`}
            action={
              <span className="text-[10px] font-medium text-slate-400 px-2 py-0.5 bg-slate-50 rounded border border-slate-200">
                {analysisMode === 'backend' ? 'Backend' : 'Local'} Engine
              </span>
            }
          />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <SummaryStat label="Processed Rows" value={lastAnalysisSummary.processedRows} icon={<CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />} />
            <SummaryStat label="Skipped Rows" value={lastAnalysisSummary.skippedRows} icon={<AlertCircle className="w-3.5 h-3.5 text-amber-500" />} />
            <SummaryStat label="Supported" value={lastAnalysisSummary.supportedAnalyses.length} icon={<CheckCircle2 className="w-3.5 h-3.5 text-teal-500" />} />
            <SummaryStat label="Unavailable" value={lastAnalysisSummary.missingAnalyses.length} icon={<AlertCircle className="w-3.5 h-3.5 text-slate-400" />} />
          </div>

          {lastAnalysisSummary.supportedAnalyses.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {lastAnalysisSummary.supportedAnalyses.map((a) => (
                <span key={a} className="px-2 py-0.5 text-[10px] bg-emerald-50 text-emerald-700 rounded border border-emerald-200">
                  {a.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                </span>
              ))}
            </div>
          )}
          {lastAnalysisSummary.missingAnalyses.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {lastAnalysisSummary.missingAnalyses.map((a) => (
                <span key={a} className="px-2 py-0.5 text-[10px] bg-amber-50 text-amber-700 rounded border border-amber-200">
                  {a.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                </span>
              ))}
            </div>
          )}
        </Panel>
      )}

      {/* Severity counts */}
      <div className="grid grid-cols-3 gap-3">
        <SeverityCard label="Critical" count={critical.length} color="red" />
        <SeverityCard label="Warnings" count={warnings.length} color="amber" />
        <SeverityCard label="Informational" count={info.length} color="teal" />
      </div>

      {/* Recommendations list */}
      <Panel>
        <PanelHeader title="Actionable Recommendations" subtitle="Prioritized by severity" />
        {recommendations.length === 0 ? (
          <EmptyState title="No recommendations" message="All metrics look healthy." icon={<Info className="w-6 h-6 text-slate-400" />} />
        ) : (
          <div className="space-y-2">
            {recommendations.map((rec) => <RecommendationCard key={rec.id} rec={rec} />)}
          </div>
        )}
      </Panel>
    </div>
  );
}

function SeverityCard({ label, count, color }: { label: string; count: number; color: 'red' | 'amber' | 'teal' }) {
  const styles = {
    red: 'bg-red-50 border-red-200 text-red-600',
    amber: 'bg-amber-50 border-amber-200 text-amber-600',
    teal: 'bg-teal-50 border-teal-200 text-teal-600',
  };
  return (
    <div className={`rounded-lg border p-3.5 ${styles[color]}`}>
      <p className="text-2xl font-bold leading-tight">{count}</p>
      <p className="text-xs opacity-80 mt-0.5">{label}</p>
    </div>
  );
}

function SummaryStat({ label, value, icon }: { label: string; value: number; icon: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2.5 bg-slate-50 rounded-lg p-2.5 border border-slate-100">
      <div className="shrink-0">{icon}</div>
      <div>
        <p className="text-base font-bold text-navy-700 leading-tight">{value}</p>
        <p className="text-[10px] text-slate-500">{label}</p>
      </div>
    </div>
  );
}

function RecommendationCard({ rec }: { rec: Recommendation }) {
  const styles = {
    critical: { border: 'border-red-200', icon: 'bg-red-100 text-red-600', Icon: AlertTriangle },
    warning: { border: 'border-amber-200', icon: 'bg-amber-100 text-amber-600', Icon: AlertCircle },
    info: { border: 'border-teal-200', icon: 'bg-teal-100 text-teal-600', Icon: Info },
  };
  const s = styles[rec.severity];
  const Icon = s.Icon;

  return (
    <div className={`bg-white rounded-lg border ${s.border} p-3 flex items-start gap-3 hover:shadow-sm transition-shadow`}>
      <div className={`w-8 h-8 rounded-lg ${s.icon} flex items-center justify-center shrink-0`}>
        <Icon className="w-4 h-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-3">
          <h4 className="text-sm font-semibold text-navy-800">{rec.title}</h4>
          <span className="text-[10px] font-medium text-slate-400 shrink-0 bg-slate-50 px-1.5 py-0.5 rounded">{rec.metric}</span>
        </div>
        <p className="text-xs text-slate-600 mt-1">{rec.description}</p>
      </div>
    </div>
  );
}
