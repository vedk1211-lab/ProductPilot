import { useData } from '@/context/useData';
import { Panel, PanelHeader } from '@/components/Panel';
import { EmptyState } from '@/components/EmptyState';
import {
  GitBranch, Database, FileSearch, Calculator, BarChart3,
  CheckCircle2, XCircle, AlertCircle, ArrowRight,
} from 'lucide-react';
import type { AnalysisDataset } from '@/data/types';

export function PipelinePage() {
  const { analysisResult, analysisDataset, analysisMode, dataSource } = useData();

  if (!analysisDataset || !analysisResult) {
    return (
      <div className="p-6">
        <EmptyState title="No analysis data" message="Run an analysis from the Data Workspace to see pipeline diagnostics." icon={<GitBranch className="w-6 h-6 text-slate-400" />} />
      </div>
    );
  }

  const stages = buildPipelineStages(analysisDataset, analysisMode, dataSource);

  return (
    <div className="p-5 space-y-4 animate-fade-in">
      {/* Pipeline flow */}
      <Panel>
        <PanelHeader title="Data Processing Pipeline" subtitle="Stages from raw input to analyzed output" />
        <div className="flex items-center gap-2 overflow-x-auto scrollbar-thin pb-2">
          {stages.map((stage, i) => (
            <div key={stage.id} className="flex items-center gap-2 shrink-0">
              <div className={`flex flex-col items-center px-3 py-2.5 rounded-lg border min-w-[120px] ${stage.status === 'ok' ? 'bg-emerald-50 border-emerald-200' : stage.status === 'warn' ? 'bg-amber-50 border-amber-200' : 'bg-slate-50 border-slate-200'}`}>
                <div className={`w-7 h-7 rounded-md flex items-center justify-center mb-1.5 ${stage.status === 'ok' ? 'bg-emerald-100 text-emerald-600' : stage.status === 'warn' ? 'bg-amber-100 text-amber-600' : 'bg-slate-100 text-slate-500'}`}>
                  {stage.icon}
                </div>
                <p className="text-[11px] font-medium text-navy-700 text-center leading-tight">{stage.label}</p>
                <p className="text-[9px] text-slate-400 mt-0.5">{stage.detail}</p>
              </div>
              {i < stages.length - 1 && <ArrowRight className="w-3.5 h-3.5 text-slate-300 shrink-0" />}
            </div>
          ))}
        </div>
      </Panel>

      {/* Dataset diagnostics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Panel>
          <PanelHeader title="Dataset Properties" subtitle="Source metadata and row counts" />
          <div className="space-y-1.5 text-xs">
            <Row label="Data Source" value={dataSource === 'sample' ? 'Sample Dataset' : 'Uploaded CSV'} />
            <Row label="Total Rows" value={String(analysisDataset.rowCount)} />
            <Row label="Valid Rows" value={String(analysisDataset.validRowCount)} />
            <Row label="Invalid / Skipped" value={String(analysisDataset.invalidRowCount)} />
            <Row label="Columns" value={String(analysisDataset.columns.length)} />
            <Row label="Mapped Fields" value={String(Object.values(analysisDataset.mappings).filter(Boolean).length)} />
            <Row label="Processing Engine" value={analysisMode === 'backend' ? 'Backend (PySpark)' : 'Local (Browser)'} />
            <Row label="Computed At" value={new Date(analysisDataset.computedAt).toLocaleString()} />
          </div>
        </Panel>

        <Panel>
          <PanelHeader title="Analysis Availability" subtitle="Supported and unavailable analyses" />
          <div className="space-y-2">
            {analysisDataset.supportedAnalyses.map((a) => (
              <div key={a} className="flex items-center gap-2 text-xs bg-emerald-50 rounded-lg p-2 border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                <span className="text-emerald-700 font-medium">{formatAnalysisName(a)}</span>
              </div>
            ))}
            {analysisDataset.unsupportedAnalyses.map((u) => (
              <div key={u.analysis} className="flex items-start gap-2 text-xs bg-amber-50 rounded-lg p-2 border border-amber-200">
                <XCircle className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <p className="text-amber-700 font-medium">{formatAnalysisName(u.analysis)}</p>
                  <p className="text-amber-600/70 mt-0.5">{u.reason}</p>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      {/* Column schema */}
      <Panel>
        <PanelHeader title="Column Schema" subtitle="Detected types and field mappings" />
        <div className="overflow-x-auto scrollbar-thin">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200">
                <Th>Column</Th>
                <Th>Type</Th>
                <Th>Mapped Field</Th>
                <Th align="right">Missing</Th>
                <Th align="right">Unique</Th>
                <Th>Sample Values</Th>
              </tr>
            </thead>
            <tbody>
              {analysisDataset.columns.map((col) => (
                <tr key={col.name} className="border-b border-slate-100 hover:bg-slate-50/40 transition-colors">
                  <td className="py-2 px-3 font-medium text-navy-700 text-xs">{col.name}</td>
                  <td className="py-2 px-3"><TypeBadge type={col.type} /></td>
                  <td className="py-2 px-3 text-xs">
                    {col.semanticField ? (
                      <span className="text-teal-600 font-medium">{col.semanticField}</span>
                    ) : (
                      <span className="text-slate-300">—</span>
                    )}
                  </td>
                  <td className="py-2 px-3 text-right text-xs">
                    {col.missingCount > 0 ? <span className="text-amber-600">{col.missingCount}</span> : <span className="text-slate-300">0</span>}
                  </td>
                  <td className="py-2 px-3 text-right text-xs text-slate-500">{col.uniqueCount}</td>
                  <td className="py-2 px-3 text-xs text-slate-400 truncate max-w-[200px]">
                    {col.sampleValues.slice(0, 3).join(', ')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      {/* Analysis output summary */}
      <Panel>
        <PanelHeader title="Analysis Output" subtitle="Computed metrics from the last run" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <OutputMetric label="Features" value={analysisResult.features.length} />
          <OutputMetric label="Tasks" value={analysisResult.tasks.length} />
          <OutputMetric label="Releases" value={analysisResult.releases.length} />
          <OutputMetric label="Alerts" value={analysisResult.alerts.length} />
          <OutputMetric label="Recommendations" value={analysisResult.recommendations.length} />
          <OutputMetric label="Avg WSJF" value={Number(analysisResult.kpis.avgWsJf.toFixed(1))} />
          <OutputMetric label="Completion Rate" value={`${analysisResult.kpis.completionRate.toFixed(0)}%`} />
          <OutputMetric label="Total Demand" value={analysisResult.kpis.totalDemand} />
        </div>
      </Panel>
    </div>
  );
}

function buildPipelineStages(ds: AnalysisDataset, mode: string, source: string) {
  return [
    {
      id: 'source',
      label: 'Data Source',
      detail: source === 'sample' ? 'Pre-loaded' : 'CSV Upload',
      icon: <Database className="w-3.5 h-3.5" />,
      status: 'ok' as const,
    },
    {
      id: 'parse',
      label: 'Parsing',
      detail: `${ds.rowCount} rows`,
      icon: <FileSearch className="w-3.5 h-3.5" />,
      status: 'ok' as const,
    },
    {
      id: 'validate',
      label: 'Validation',
      detail: `${ds.invalidRowCount} skipped`,
      icon: <AlertCircle className="w-3.5 h-3.5" />,
      status: (ds.invalidRowCount > 0 ? 'warn' : 'ok') as 'ok' | 'warn',
    },
    {
      id: 'map',
      label: 'Field Mapping',
      detail: `${Object.values(ds.mappings).filter(Boolean).length} fields`,
      icon: <GitBranch className="w-3.5 h-3.5" />,
      status: (ds.unsupportedAnalyses.length > 0 ? 'warn' : 'ok') as 'ok' | 'warn',
    },
    {
      id: 'analyze',
      label: 'Analysis',
      detail: mode === 'backend' ? 'PySpark' : 'Local',
      icon: <Calculator className="w-3.5 h-3.5" />,
      status: 'ok' as const,
    },
    {
      id: 'output',
      label: 'Output',
      detail: `${ds.supportedAnalyses.length} analyses`,
      icon: <BarChart3 className="w-3.5 h-3.5" />,
      status: 'ok' as const,
    },
  ];
}

function formatAnalysisName(a: string): string {
  return a.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-1 border-b border-slate-50 last:border-0">
      <span className="text-slate-400">{label}</span>
      <span className="font-medium text-slate-700">{value}</span>
    </div>
  );
}

function TypeBadge({ type }: { type: string }) {
  const styles: Record<string, string> = {
    number: 'bg-blue-100 text-blue-700 border-blue-200',
    date: 'bg-purple-100 text-purple-700 border-purple-200',
    string: 'bg-slate-100 text-slate-600 border-slate-200',
    boolean: 'bg-teal-100 text-teal-700 border-teal-200',
  };
  return <span className={`inline-block px-1.5 py-0.5 text-[10px] font-medium rounded border ${styles[type] ?? styles.string}`}>{type}</span>;
}

function OutputMetric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-slate-50 rounded-lg p-2.5 border border-slate-100">
      <p className="text-base font-bold text-navy-700 leading-tight">{value}</p>
      <p className="text-[10px] text-slate-500 mt-0.5">{label}</p>
    </div>
  );
}

function Th({ children, align = 'left' }: { children: React.ReactNode; align?: 'left' | 'right' }) {
  return (
    <th className={`py-2 px-3 font-medium text-slate-500 text-[11px] uppercase tracking-wide ${align === 'right' ? 'text-right' : 'text-left'}`}>
      {children}
    </th>
  );
}
