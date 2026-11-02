import { useState, useMemo } from 'react';
import { AlertTriangle, Clock, XCircle, Search, X, ShieldAlert } from 'lucide-react';
import { useData } from '@/context/useData';
import { EmptyState } from '@/components/EmptyState';
import { Panel, PanelHeader } from '@/components/Panel';
import { DonutChart } from '@/components/charts/DonutChart';
import { BarChart } from '@/components/charts/BarChart';
import type { TaskRow, ReleaseHealth } from '@/data/types';

export function TaskRiskPage() {
  const { analysisResult, analysisDataset } = useData();
  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState<'all' | 'High' | 'Medium' | 'Low' | 'N/A'>('all');
  const [selectedTask, setSelectedTask] = useState<TaskRow | null>(null);

  const filteredTasks = useMemo(() => {
    if (!analysisResult) return [];
    const sorted = [...analysisResult.tasks].sort((a, b) => b.riskScore - a.riskScore);
    return sorted.filter((t) => {
      if (riskFilter !== 'all' && t.riskLevel !== riskFilter) return false;
      if (search && !t.id.toLowerCase().includes(search.toLowerCase()) && !t.projectId.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [analysisResult, riskFilter, search]);

  if (!analysisResult || !analysisDataset) {
    return <div className="p-6"><EmptyState title="No data" message="Run an analysis to see task risk." icon={<AlertTriangle className="w-6 h-6 text-slate-400" />} /></div>;
  }

  if (analysisResult.tasks.length === 0) {
    return (
      <div className="p-6">
        <EmptyState
          title="Task risk analysis unavailable"
          message="This analysis requires task ID, task status, and planned completion date. Map these fields in the Data Workspace."
          requiredFields={['Task ID', 'Task Status', 'Planned Date']}
          icon={<AlertTriangle className="w-6 h-6 text-slate-400" />}
        />
      </div>
    );
  }

  const { tasks, kpis, releases, riskDistribution, statusDistribution } = analysisResult;
  const completed = tasks.filter((t) => /complete|done|closed|resolved/i.test(t.status)).length;

  return (
    <div className="p-5 space-y-4 animate-fade-in">
      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <RiskSummaryCard label="High Risk" value={kpis.highRiskTasks} icon={<AlertTriangle className="w-4 h-4" />} color="red" />
        <RiskSummaryCard label="Overdue" value={kpis.overdueTasks} icon={<Clock className="w-4 h-4" />} color="amber" />
        <RiskSummaryCard label="Completed" value={completed} icon={<XCircle className="w-4 h-4" />} color="green" />
        <RiskSummaryCard label="Completion Rate" value={`${kpis.completionRate.toFixed(0)}%`} icon={<Clock className="w-4 h-4" />} color="navy" />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Panel>
          <PanelHeader title="Risk Distribution" subtitle="By risk level" />
          <DonutChart data={riskDistribution} centerValue={String(kpis.totalTasks)} centerLabel="Tasks" size={140} />
        </Panel>
        <Panel>
          <PanelHeader title="Task Status Breakdown" subtitle="Current workflow states" />
          <BarChart data={statusDistribution} height={180} />
        </Panel>
        <Panel>
          <PanelHeader title="Release Health" subtitle="Completion & risk per release" />
          <div className="space-y-2">
            {releases.map((r) => <ReleaseHealthRow key={r.releaseId} release={r} />)}
          </div>
        </Panel>
      </div>

      {/* Task table with filters */}
      <Panel>
        <div className="flex items-center gap-3 mb-3 flex-wrap">
          <PanelHeader title="Task Risk Register" subtitle="Sorted by risk score (highest first)" />
          <div className="flex-1" />
          <div className="relative min-w-[180px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search tasks…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-400/30 focus:border-teal-400"
            />
          </div>
          <div className="flex items-center gap-1.5">
            {(['all', 'High', 'Medium', 'Low', 'N/A'] as const).map((r) => (
              <button
                key={r}
                onClick={() => setRiskFilter(r)}
                className={`px-2.5 py-1.5 text-xs font-medium rounded-md transition-colors ${
                  riskFilter === r ? 'bg-navy-600 text-white' : 'bg-slate-50 text-slate-600 border border-slate-200 hover:bg-slate-100'
                }`}
              >
                {r === 'all' ? 'All' : r}
              </button>
            ))}
          </div>
          <span className="text-xs text-slate-400">{filteredTasks.length} of {tasks.length}</span>
        </div>

        <div className="overflow-x-auto scrollbar-thin">
          <table className="w-full text-sm">
            <thead className="bg-slate-50/60 border-b border-slate-200">
              <tr>
                <Th>Task ID</Th>
                <Th>Project</Th>
                <Th>Status</Th>
                <Th>Planned</Th>
                <Th>Actual</Th>
                <Th align="right">Overdue</Th>
                <Th align="right">Risk</Th>
                <Th>Level</Th>
                <Th> </Th>
              </tr>
            </thead>
            <tbody>
              {filteredTasks.map((t) => (
                <tr
                  key={t.id}
                  onClick={() => setSelectedTask(t)}
                  className="border-b border-slate-100 hover:bg-slate-50/40 transition-colors cursor-pointer"
                >
                  <td className="py-2.5 px-3 font-medium text-navy-700">{t.id}</td>
                  <td className="py-2.5 px-3 text-slate-600">{t.projectId}</td>
                  <td className="py-2.5 px-3"><StatusBadge status={t.status} /></td>
                  <td className="py-2.5 px-3 text-slate-500 text-xs">{t.plannedDate ?? '—'}</td>
                  <td className="py-2.5 px-3 text-slate-500 text-xs">{t.actualDate ?? '—'}</td>
                  <td className={`py-2.5 px-3 text-right font-medium text-xs ${t.daysOverdue > 0 ? 'text-red-600' : 'text-slate-400'}`}>
                    {t.daysOverdue > 0 ? `${t.daysOverdue}d` : '—'}
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    <span className={`font-bold text-xs ${t.riskScore >= 50 ? 'text-red-600' : t.riskScore >= 25 ? 'text-amber-600' : 'text-slate-500'}`}>
                      {t.riskScore}
                    </span>
                  </td>
                  <td className="py-2.5 px-3"><RiskLevelBadge level={t.riskLevel} /></td>
                  <td className="py-2.5 px-3 text-right">
                    <ShieldAlert className="w-3.5 h-3.5 text-slate-300 inline" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filteredTasks.length === 0 && (
          <div className="py-8 text-center text-sm text-slate-400">No tasks match the current filters.</div>
        )}
      </Panel>

      {selectedTask && <TaskDrawer task={selectedTask} onClose={() => setSelectedTask(null)} />}
    </div>
  );
}

function ReleaseHealthRow({ release }: { release: ReleaseHealth }) {
  const healthStyles = {
    Healthy: 'text-emerald-600 bg-emerald-50 border-emerald-200',
    'At Risk': 'text-amber-600 bg-amber-50 border-amber-200',
    Critical: 'text-red-600 bg-red-50 border-red-200',
  };
  return (
    <div className="flex items-center gap-2.5 py-1.5 border-b border-slate-100 last:border-0">
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium text-navy-700 truncate">{release.releaseId}</p>
        <p className="text-[10px] text-slate-400">{release.totalTasks} tasks · {release.overdueTasks} overdue</p>
      </div>
      <div className="w-20 h-1.5 bg-slate-100 rounded-full overflow-hidden shrink-0">
        <div
          className={`h-full rounded-full ${release.health === 'Healthy' ? 'bg-emerald-500' : release.health === 'At Risk' ? 'bg-amber-500' : 'bg-red-500'}`}
          style={{ width: `${release.completionRate}%` }}
        />
      </div>
      <span className="text-xs font-semibold text-slate-600 w-10 text-right shrink-0">{release.completionRate.toFixed(0)}%</span>
      <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded border ${healthStyles[release.health]} shrink-0`}>
        {release.health}
      </span>
    </div>
  );
}

function TaskDrawer({ task, onClose }: { task: TaskRow; onClose: () => void }) {
  return (
    <>
      <div className="fixed inset-0 bg-black/30 z-30" onClick={onClose} />
      <div className="fixed right-0 top-0 h-full w-[400px] bg-white shadow-xl z-40 animate-slide-in-right overflow-y-auto scrollbar-thin">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200">
          <div>
            <p className="text-[10px] text-slate-400 font-medium uppercase tracking-wide">Task Detail</p>
            <h3 className="text-base font-semibold text-navy-800 mt-0.5">{task.id}</h3>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="p-5 space-y-5">
          <div className="grid grid-cols-2 gap-3">
            <Stat label="Risk Score" value={String(task.riskScore)} accent={task.riskScore >= 50 ? 'red' : task.riskScore >= 25 ? 'amber' : 'slate'} />
            <Stat label="Risk Level" value={task.riskLevel} accent={task.riskLevel === 'High' ? 'red' : task.riskLevel === 'Medium' ? 'amber' : 'slate'} />
            <Stat label="Days Overdue" value={task.daysOverdue > 0 ? `${task.daysOverdue}d` : 'On track'} accent={task.daysOverdue > 0 ? 'red' : 'green'} />
            <Stat label="Status" value={task.status} accent="slate" />
          </div>

          <div>
            <h4 className="text-xs font-semibold text-navy-700 mb-2">Risk Score Breakdown</h4>
            {task.riskReasons.length > 0 ? (
              <div className="space-y-1.5">
                {task.riskReasons.map((reason, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-slate-600 bg-slate-50 rounded-lg p-2.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
                    <span>{reason}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex items-center gap-2 text-xs text-emerald-600 bg-emerald-50 rounded-lg p-2.5">
                <XCircle className="w-3.5 h-3.5" />
                <span>No risk factors detected. Task is on track.</span>
              </div>
            )}
          </div>

          <div>
            <h4 className="text-xs font-semibold text-navy-700 mb-2">Schedule</h4>
            <div className="space-y-1.5 text-xs">
              <Row label="Project" value={task.projectId} />
              <Row label="Planned Date" value={task.plannedDate ?? 'Not set'} />
              <Row label="Actual Date" value={task.actualDate ?? 'Not completed'} />
              <Row label="Release" value={task.releaseId ?? 'Unassigned'} />
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent: 'red' | 'amber' | 'green' | 'slate' }) {
  const styles = {
    red: 'bg-red-50 border-red-200 text-red-600',
    amber: 'bg-amber-50 border-amber-200 text-amber-600',
    green: 'bg-emerald-50 border-emerald-200 text-emerald-600',
    slate: 'bg-slate-50 border-slate-200 text-navy-700',
  };
  return (
    <div className={`rounded-lg p-3 border ${styles[accent]}`}>
      <p className="text-sm font-bold leading-tight">{value}</p>
      <p className="text-[11px] opacity-70 mt-0.5">{label}</p>
    </div>
  );
}

function RiskSummaryCard({ label, value, icon, color }: { label: string; value: string | number; icon: React.ReactNode; color: 'red' | 'amber' | 'green' | 'navy' }) {
  const styles = {
    red: 'bg-red-50 border-red-200 text-red-600',
    amber: 'bg-amber-50 border-amber-200 text-amber-600',
    green: 'bg-emerald-50 border-emerald-200 text-emerald-600',
    navy: 'bg-navy-50 border-navy-100 text-navy-600',
  };
  return (
    <div className={`rounded-lg border p-3.5 flex items-center gap-3 ${styles[color]}`}>
      <div className="w-8 h-8 rounded-md bg-white/60 flex items-center justify-center shrink-0">{icon}</div>
      <div>
        <p className="text-xl font-bold leading-tight">{value}</p>
        <p className="text-xs opacity-80">{label}</p>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const isComplete = /complete|done|closed|resolved/i.test(status);
  const isInProgress = /progress|active|doing/i.test(status);
  const isNotStarted = /not started|backlog|open|new/i.test(status);
  const cls = isComplete
    ? 'bg-emerald-100 text-emerald-700 border-emerald-200'
    : isInProgress
    ? 'bg-teal-100 text-teal-700 border-teal-200'
    : isNotStarted
    ? 'bg-slate-100 text-slate-600 border-slate-200'
    : 'bg-amber-100 text-amber-700 border-amber-200';
  return <span className={`inline-block px-2 py-0.5 text-[10px] font-medium rounded border ${cls}`}>{status}</span>;
}

function RiskLevelBadge({ level }: { level: 'High' | 'Medium' | 'Low' | 'N/A' }) {
  const styles = {
    High: 'bg-red-100 text-red-700 border-red-200',
    Medium: 'bg-amber-100 text-amber-700 border-amber-200',
    Low: 'bg-lime-100 text-lime-700 border-lime-200',
    'N/A': 'bg-slate-100 text-slate-500 border-slate-200',
  };
  return <span className={`inline-block px-2 py-0.5 text-[10px] font-medium rounded border ${styles[level]}`}>{level}</span>;
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-slate-400">{label}</span>
      <span className="font-medium text-slate-700">{value}</span>
    </div>
  );
}

function Th({ children, align = 'left' }: { children: React.ReactNode; align?: 'left' | 'right' }) {
  return (
    <th className={`py-2.5 px-3 font-medium text-slate-500 text-[11px] uppercase tracking-wide ${align === 'right' ? 'text-right' : 'text-left'}`}>
      {children}
    </th>
  );
}
