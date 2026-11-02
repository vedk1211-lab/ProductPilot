import {
  BarChart3, AlertTriangle, CheckCircle2, Target, Zap, TrendingUp,
  Clock, Users, FolderGit2, Bell,
} from 'lucide-react';
import { useData } from '@/context/useData';
import { BarChart } from '@/components/charts/BarChart';
import { DonutChart } from '@/components/charts/DonutChart';
import { LineChart } from '@/components/charts/LineChart';
import { EmptyState } from '@/components/EmptyState';
import { Panel, PanelHeader } from '@/components/Panel';
import type { FeatureRow, AlertItem } from '@/data/types';

export function DashboardPage() {
  const { analysisResult } = useData();

  if (!analysisResult) {
    return (
      <div className="p-6">
        <EmptyState title="No analysis data available" message="Run an analysis from the Data Workspace to see dashboard metrics." icon={<BarChart3 className="w-6 h-6 text-slate-400" />} />
      </div>
    );
  }

  const { kpis, priorityDistribution, riskDistribution, demandTrend, releaseComparison, features, alerts, recommendations } = analysisResult;
  const hasFeatures = features.length > 0;
  const hasTasks = analysisResult.tasks.length > 0;
  const hasReleases = analysisResult.releases.length > 0;

  return (
    <div className="p-5 space-y-5 animate-fade-in">
      {/* KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        <CompactKpi label="Feature Requests" value={kpis.totalDemand} icon={<Users className="w-4 h-4" />} accent="navy" />
        <CompactKpi label="Features Analyzed" value={kpis.totalFeatures} icon={<Target className="w-4 h-4" />} accent="teal" />
        <CompactKpi label="Open Tasks" value={kpis.openTasks} icon={<Clock className="w-4 h-4" />} accent="amber" />
        <CompactKpi label="Overdue Tasks" value={kpis.overdueTasks} icon={<AlertTriangle className="w-4 h-4" />} accent={kpis.overdueTasks > 0 ? 'red' : 'green'} />
        <CompactKpi label="High-Risk Releases" value={kpis.highRiskReleases} icon={<FolderGit2 className="w-4 h-4" />} accent={kpis.highRiskReleases > 0 ? 'red' : 'green'} />
      </div>

      {/* Row: Trends (8) + Priority (4) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <Panel className="lg:col-span-8">
          <PanelHeader title="Feature Request Trends" subtitle="Total customer demand grouped by release" />
          {hasFeatures && demandTrend.length > 0 ? (
            <LineChart data={demandTrend} height={220} color="#1e3a70" />
          ) : (
            <EmptyChartState message="Demand trend requires features with release assignments." />
          )}
        </Panel>

        <Panel className="lg:col-span-4">
          <PanelHeader title="Feature Priority Distribution" subtitle="Ranked by WSJF score" />
          {hasFeatures ? (
            <DonutChart data={priorityDistribution} centerValue={String(kpis.totalFeatures)} centerLabel="Features" size={150} />
          ) : (
            <EmptyChartState message="Feature prioritization requires demand, value, and effort columns." />
          )}
        </Panel>
      </div>

      {/* Row: Risk (4) + Release Perf (4) + Top Features Table (4) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <Panel className="lg:col-span-4">
          <PanelHeader title="Task Risk Distribution" subtitle="Schedule risk breakdown" />
          {hasTasks ? (
            <DonutChart data={riskDistribution} centerValue={String(kpis.totalTasks)} centerLabel="Tasks" size={150} />
          ) : (
            <EmptyChartState message="Task risk requires task ID, status, and planned date." />
          )}
        </Panel>

        <Panel className="lg:col-span-4">
          <PanelHeader title="Release Performance" subtitle="Completion rate per release" />
          {hasReleases ? (
            <BarChart data={releaseComparison} height={200} valueFormatter={(v) => `${v.toFixed(0)}%`} />
          ) : (
            <EmptyChartState message="Release performance requires tasks with release assignments." />
          )}
        </Panel>

        <Panel className="lg:col-span-4">
          <PanelHeader title="Top Priority Features" subtitle="Highest WSJF scores" />
          {hasFeatures ? (
            <div className="space-y-2">
              {features.slice(0, 5).map((f) => (
                <div key={f.id} className="flex items-center gap-2.5 py-1.5 border-b border-slate-100 last:border-0">
                  <div className="w-6 h-6 rounded bg-navy-50 text-navy-600 text-[10px] font-bold flex items-center justify-center shrink-0">
                    {f.priorityRank}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium text-navy-700 truncate">{f.name}</p>
                    <p className="text-[10px] text-slate-400">{f.releaseId ?? 'Unassigned'}</p>
                  </div>
                  <span className="text-xs font-bold text-teal-600 shrink-0">{f.wsjfScore.toFixed(1)}</span>
                  <PriorityBadge label={f.priorityLabel} />
                </div>
              ))}
            </div>
          ) : (
            <EmptyChartState message="No features available for ranking." />
          )}
        </Panel>
      </div>

      {/* Row: Alerts (6) + Recommendations (6) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <Panel className="lg:col-span-6">
          <PanelHeader title="Recent Alerts" subtitle={`${alerts.length} alert${alerts.length !== 1 ? 's' : ''} detected`} action={<Bell className="w-4 h-4 text-slate-400" />} />
          {alerts.length > 0 ? (
            <div className="space-y-2 max-h-[280px] overflow-y-auto scrollbar-thin pr-1">
              {alerts.slice(0, 8).map((a) => <AlertRow key={a.id} alert={a} />)}
            </div>
          ) : (
            <div className="flex items-center gap-2 py-6 text-sm text-emerald-600">
              <CheckCircle2 className="w-4 h-4" />
              <span>No active alerts. All metrics within healthy range.</span>
            </div>
          )}
        </Panel>

        <Panel className="lg:col-span-6">
          <PanelHeader title="Management Recommendations" subtitle="Top action items" action={<Zap className="w-4 h-4 text-teal-500" />} />
          {recommendations.length > 0 ? (
            <div className="space-y-2 max-h-[280px] overflow-y-auto scrollbar-thin pr-1">
              {recommendations.slice(0, 6).map((rec) => (
                <div key={rec.id} className="flex items-start gap-2.5 py-1.5 border-b border-slate-100 last:border-0">
                  <RecDot severity={rec.severity} />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium text-navy-700">{rec.title}</p>
                    <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-2">{rec.description}</p>
                  </div>
                  <span className="text-[10px] text-slate-400 shrink-0">{rec.metric}</span>
                </div>
              ))}
            </div>
          ) : (
            <EmptyChartState message="No recommendations at this time." />
          )}
        </Panel>
      </div>

      {/* Full-width feature table */}
      {hasFeatures && (
        <Panel>
          <PanelHeader title="Top 10 Prioritized Features" subtitle="Complete ranking with scoring breakdown" />
          <div className="overflow-x-auto scrollbar-thin">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200">
                  <Th>Rank</Th>
                  <Th>Feature</Th>
                  <Th align="right">WSJF</Th>
                  <Th align="right">Demand</Th>
                  <Th align="right">Value</Th>
                  <Th align="right">Effort</Th>
                  <Th>Release</Th>
                  <Th>Priority</Th>
                </tr>
              </thead>
              <tbody>
                {features.slice(0, 10).map((f: FeatureRow) => (
                  <tr key={f.id} className="border-b border-slate-100 hover:bg-slate-50/40 transition-colors">
                    <td className="py-2 px-3 font-semibold text-navy-700">#{f.priorityRank}</td>
                    <td className="py-2 px-3 text-slate-700 font-medium">{f.name}</td>
                    <td className="py-2 px-3 text-right font-bold text-teal-600">{f.wsjfScore.toFixed(2)}</td>
                    <td className="py-2 px-3 text-right text-slate-600">{f.customerDemand}</td>
                    <td className="py-2 px-3 text-right text-slate-600">{f.businessValue.toFixed(1)}</td>
                    <td className="py-2 px-3 text-right text-slate-600">{f.devEffort}</td>
                    <td className="py-2 px-3 text-slate-500 text-xs">{f.releaseId ?? '—'}</td>
                    <td className="py-2 px-3"><PriorityBadge label={f.priorityLabel} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}
    </div>
  );
}

function CompactKpi({ label, value, icon, accent }: { label: string; value: number; icon: React.ReactNode; accent: 'navy' | 'teal' | 'amber' | 'red' | 'green' }) {
  const styles = {
    navy: 'bg-navy-50 text-navy-600',
    teal: 'bg-teal-50 text-teal-600',
    amber: 'bg-amber-50 text-amber-600',
    red: 'bg-red-50 text-red-600',
    green: 'bg-emerald-50 text-emerald-600',
  };
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-3.5 hover:shadow-sm transition-shadow">
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-7 h-7 rounded-md flex items-center justify-center ${styles[accent]}`}>
          {icon}
        </div>
      </div>
      <p className="text-xl font-bold text-navy-800 leading-tight">{value}</p>
      <p className="text-xs text-slate-500 mt-0.5">{label}</p>
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

function AlertRow({ alert }: { alert: AlertItem }) {
  const styles = {
    critical: { dot: 'bg-red-500', text: 'text-red-700', label: 'Critical' },
    warning: { dot: 'bg-amber-500', text: 'text-amber-700', label: 'Warning' },
    info: { dot: 'bg-teal-500', text: 'text-teal-700', label: 'Info' },
  };
  const s = styles[alert.severity];
  return (
    <div className="flex items-start gap-2.5 py-1.5 border-b border-slate-100 last:border-0">
      <div className={`w-2 h-2 rounded-full ${s.dot} mt-1.5 shrink-0`} />
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium text-navy-700">{alert.title}</p>
        <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-2">{alert.message}</p>
      </div>
      <span className={`text-[10px] font-medium ${s.text} shrink-0`}>{s.label}</span>
    </div>
  );
}

function RecDot({ severity }: { severity: 'critical' | 'warning' | 'info' }) {
  const color = severity === 'critical' ? 'bg-red-500' : severity === 'warning' ? 'bg-amber-500' : 'bg-teal-500';
  return <div className={`w-2 h-2 rounded-full ${color} mt-1.5 shrink-0`} />;
}

function EmptyChartState({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center py-10 text-center">
      <p className="text-xs text-slate-400 max-w-[240px]">{message}</p>
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
