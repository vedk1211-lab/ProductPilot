import type {
  AnalysisDataset,
  AnalysisResult,
  ChartData,
  ColumnMapping,
  FeatureRow,
  KpiSummary,
  Recommendation,
  TaskRow,
  UploadedDataset,
  ValidationIssue,
  SemanticField,
  ReleaseHealth,
  AlertItem,
  TrendPoint,
  ScoringWeights,
} from './types';
import {
  SAMPLE_CSV_HEADERS,
  SAMPLE_CSV_ROWS,
  getSampleColumnSchemas,
} from './sampleData';

function toNum(v: string | undefined | null): number | null {
  if (v === undefined || v === null || v === '') return null;
  const n = Number(v);
  return isNaN(n) ? null : n;
}

function toDate(v: string | undefined | null): string | null {
  if (!v || v === '') return null;
  const d = new Date(v);
  return isNaN(d.getTime()) ? null : d.toISOString().split('T')[0];
}

function daysBetween(a: string | null, b: string | null): number {
  if (!a || !b) return 0;
  const da = new Date(a);
  const db = new Date(b);
  return Math.round((db.getTime() - da.getTime()) / (1000 * 60 * 60 * 24));
}

function priorityLabel(score: number, max: number): FeatureRow['priorityLabel'] {
  const ratio = score / max;
  if (ratio >= 0.75) return 'Critical';
  if (ratio >= 0.5) return 'High';
  if (ratio >= 0.25) return 'Medium';
  return 'Low';
}

export const DEFAULT_WEIGHTS: ScoringWeights = {
  businessValue: 1,
  urgency: 1,
  strategicAlignment: 1,
  customerDemand: 0.1,
  devEffort: 1,
};

export function getSampleAnalysisDataset(): AnalysisDataset {
  const columns = getSampleColumnSchemas();
  const mappings: ColumnMapping = {};
  for (const col of columns) {
    if (col.semanticField) mappings[col.name] = col.semanticField;
  }

  const rows = SAMPLE_CSV_ROWS.map((row) => {
    const obj: Record<string, string | number | null> = {};
    SAMPLE_CSV_HEADERS.forEach((h, i) => {
      obj[h] = row[i] ?? '';
    });
    return obj;
  });

  return {
    source: 'sample',
    rowCount: rows.length,
    validRowCount: rows.length,
    invalidRowCount: 0,
    columns,
    rows,
    mappings,
    supportedAnalyses: ['feature-prioritization', 'task-risk', 'recommendations', 'kpi-summary'],
    unsupportedAnalyses: [],
    computedAt: Date.now(),
  };
}

export function buildAnalysisDataset(
  dataset: UploadedDataset,
  mappings: ColumnMapping
): AnalysisDataset {
  const fieldToColumn = new Map<SemanticField, string>();
  for (const [col, field] of Object.entries(mappings)) {
    if (field) fieldToColumn.set(field, col);
  }

  const has = (f: SemanticField) => fieldToColumn.has(f);

  const supportedAnalyses: string[] = [];
  const unsupportedAnalyses: AnalysisDataset['unsupportedAnalyses'] = [];

  if (has('customerDemand') && has('businessValue') && has('devEffort')) {
    supportedAnalyses.push('feature-prioritization');
  } else {
    unsupportedAnalyses.push({
      analysis: 'feature-prioritization',
      reason: 'Requires customer demand, business value, and dev effort columns.',
      requiredFields: ['customerDemand', 'businessValue', 'devEffort'],
    });
  }

  if (has('taskId') && has('taskStatus') && has('plannedDate')) {
    supportedAnalyses.push('task-risk');
  } else {
    unsupportedAnalyses.push({
      analysis: 'task-risk',
      reason: 'Requires task ID, task status, and planned completion date.',
      requiredFields: ['taskId', 'taskStatus', 'plannedDate'],
    });
  }

  supportedAnalyses.push('kpi-summary');

  const rows: Record<string, string | number | boolean | null>[] = [];
  let validRowCount = 0;
  let invalidRowCount = 0;

  for (const rawRow of dataset.rawRows) {
    const obj: Record<string, string | number | boolean | null> = {};
    let valid = true;
    dataset.rawHeaders.forEach((h, i) => {
      const val = rawRow[i] ?? '';
      obj[h] = val;
      const col = dataset.columns.find((c) => c.name === h);
      if (col && col.type === 'number') {
        const n = toNum(val);
        if (n === null && val !== '' && col.semanticField) {
          valid = false;
        }
      }
    });
    if (valid) {
      rows.push(obj);
      validRowCount++;
    } else {
      invalidRowCount++;
    }
  }

  return {
    source: 'uploaded',
    rowCount: dataset.rowCount,
    validRowCount,
    invalidRowCount,
    columns: dataset.columns,
    rows,
    mappings,
    supportedAnalyses,
    unsupportedAnalyses,
    computedAt: Date.now(),
  };
}

export function runAnalysis(dataset: AnalysisDataset, weights: ScoringWeights = DEFAULT_WEIGHTS): AnalysisResult {
  const fieldToColumn = new Map<SemanticField, string>();
  for (const [col, field] of Object.entries(dataset.mappings)) {
    if (field) fieldToColumn.set(field, col);
  }

  const col = (f: SemanticField): string | undefined => fieldToColumn.get(f);
  const val = (row: Record<string, string | number | boolean | null>, f: SemanticField): string => {
    const c = col(f);
    if (!c) return '';
    return String(row[c] ?? '');
  };

  const features: FeatureRow[] = [];
  const tasks: TaskRow[] = [];

  const today = new Date();

  for (const row of dataset.rows) {
    if (dataset.supportedAnalyses.includes('feature-prioritization')) {
      const demand = toNum(val(row, 'customerDemand')) ?? 0;
      const bizValue = toNum(val(row, 'businessValue')) ?? 0;
      const urgency = toNum(val(row, 'urgency')) ?? 5;
      const strategic = toNum(val(row, 'strategicAlignment')) ?? 3;
      const effort = toNum(val(row, 'devEffort')) ?? 1;
      const wsjf = effort > 0
        ? ((bizValue * weights.businessValue + urgency * weights.urgency + strategic * weights.strategicAlignment) * (1 + demand * weights.customerDemand)) / (effort * weights.devEffort)
        : 0;
      const id = val(row, 'featureId') || `F-${features.length + 1}`;
      const name = val(row, 'featureName') || id;
      const releaseId = val(row, 'releaseId') || null;
      const taskId = val(row, 'taskId') || null;
      features.push({
        id,
        name,
        customerDemand: demand,
        businessValue: bizValue,
        urgency,
        strategicAlignment: strategic,
        devEffort: effort,
        wsjfScore: wsjf,
        priorityRank: 0,
        priorityLabel: 'Low',
        releaseId,
        taskId,
      });
    }

    if (dataset.supportedAnalyses.includes('task-risk')) {
      const taskId = val(row, 'taskId') || `T-${tasks.length + 1}`;
      const projectId = val(row, 'projectId') || 'N/A';
      const status = val(row, 'taskStatus') || 'Unknown';
      const planned = toDate(val(row, 'plannedDate'));
      const actual = toDate(val(row, 'actualDate'));
      const releaseId = val(row, 'releaseId') || null;
      const isComplete = /complete|done|closed|resolved/i.test(status);
      let daysOverdue = 0;
      let riskScore = 0;
      const riskReasons: string[] = [];

      if (planned) {
        const referenceDate = actual ? new Date(actual) : today;
        const diff = daysBetween(planned, referenceDate.toISOString().split('T')[0]);
        daysOverdue = diff > 0 ? diff : 0;
        if (daysOverdue > 0) {
          riskScore = Math.min(100, daysOverdue * 3);
          riskReasons.push(`${daysOverdue} days overdue`);
        }
        if (!isComplete && diff > 0) {
          riskScore += 20;
          riskReasons.push('Task incomplete and past planned date');
        }
        if (isComplete && diff > 7) {
          riskScore += 10;
          riskReasons.push(`Completed ${diff} days late`);
        }
      }
      if (!isComplete && !planned) {
        riskReasons.push('No planned completion date');
      }

      let riskLevel: TaskRow['riskLevel'] = 'N/A';
      if (riskScore >= 50) riskLevel = 'High';
      else if (riskScore >= 25) riskLevel = 'Medium';
      else if (riskScore > 0) riskLevel = 'Low';

      tasks.push({
        id: taskId,
        projectId,
        status,
        plannedDate: planned,
        actualDate: actual,
        daysOverdue,
        riskLevel,
        riskScore: Math.min(100, riskScore),
        riskReasons,
        releaseId,
      });
    }
  }

  features.sort((a, b) => b.wsjfScore - a.wsjfScore);
  const maxWsJf = features.length > 0 ? features[0].wsjfScore : 1;
  features.forEach((f, i) => {
    f.priorityRank = i + 1;
    f.priorityLabel = priorityLabel(f.wsjfScore, maxWsJf);
  });

  const priorityDistribution: ChartData[] = [
    { label: 'Critical', value: features.filter((f) => f.priorityLabel === 'Critical').length, color: '#dc2626' },
    { label: 'High', value: features.filter((f) => f.priorityLabel === 'High').length, color: '#ea580c' },
    { label: 'Medium', value: features.filter((f) => f.priorityLabel === 'Medium').length, color: '#d97706' },
    { label: 'Low', value: features.filter((f) => f.priorityLabel === 'Low').length, color: '#65a30d' },
  ];

  const valueEffortScatter = features.map((f) => ({
    label: f.name,
    x: f.devEffort,
    y: f.businessValue,
    size: f.customerDemand,
  }));

  const riskDistribution: ChartData[] = [
    { label: 'High Risk', value: tasks.filter((t) => t.riskLevel === 'High').length, color: '#dc2626' },
    { label: 'Medium Risk', value: tasks.filter((t) => t.riskLevel === 'Medium').length, color: '#d97706' },
    { label: 'Low Risk', value: tasks.filter((t) => t.riskLevel === 'Low').length, color: '#65a30d' },
    { label: 'N/A', value: tasks.filter((t) => t.riskLevel === 'N/A').length, color: '#94a3b8' },
  ];

  const statusValues = tasks.map((t) => t.status);
  const statusSet = new Set(statusValues);
  const statusColors = ['#1e3a70', '#14b8a6', '#f59e0b', '#64748b', '#8b5cf6', '#ec4899'];
  const statusDistribution: ChartData[] = Array.from(statusSet).map((s, i) => ({
    label: s,
    value: statusValues.filter((v) => v === s).length,
    color: statusColors[i % statusColors.length],
  }));

  // Release health
  const releaseMap = new Map<string, TaskRow[]>();
  for (const t of tasks) {
    const key = t.releaseId ?? 'Unassigned';
    if (!releaseMap.has(key)) releaseMap.set(key, []);
    releaseMap.get(key)!.push(t);
  }
  const releases: ReleaseHealth[] = Array.from(releaseMap.entries()).map(([releaseId, releaseTasks]) => {
    const completed = releaseTasks.filter((t) => /complete|done|closed|resolved/i.test(t.status)).length;
    const overdue = releaseTasks.filter((t) => t.daysOverdue > 0).length;
    const highRisk = releaseTasks.filter((t) => t.riskLevel === 'High').length;
    const completionRate = releaseTasks.length > 0 ? (completed / releaseTasks.length) * 100 : 0;
    const riskScore = Math.min(100, overdue * 10 + highRisk * 20);
    let health: ReleaseHealth['health'] = 'Healthy';
    if (riskScore >= 50 || completionRate < 30) health = 'Critical';
    else if (riskScore >= 25 || completionRate < 60) health = 'At Risk';
    return { releaseId, totalTasks: releaseTasks.length, completedTasks: completed, overdueTasks: overdue, highRiskTasks: highRisk, completionRate, riskScore, health };
  });

  // Demand trend — group features by release and sum demand
  const demandByRelease = new Map<string, number>();
  for (const f of features) {
    const key = f.releaseId ?? 'Unassigned';
    demandByRelease.set(key, (demandByRelease.get(key) ?? 0) + f.customerDemand);
  }
  const demandTrend: TrendPoint[] = Array.from(demandByRelease.entries())
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([label, value]) => ({ label, value }));

  // Release comparison chart
  const releaseComparison: ChartData[] = releases.map((r) => ({
    label: r.releaseId,
    value: r.completionRate,
    color: r.health === 'Healthy' ? '#14b8a6' : r.health === 'At Risk' ? '#f59e0b' : '#dc2626',
  }));

  // Alerts
  const alerts: AlertItem[] = [];
  const now = Date.now();
  for (const t of tasks) {
    if (t.riskLevel === 'High') {
      alerts.push({ id: `alert-${t.id}`, severity: 'critical', title: `High-risk task: ${t.id}`, message: t.riskReasons.join('; ') || 'Significant schedule slippage detected', source: t.projectId, timestamp: now });
    }
  }
  for (const r of releases) {
    if (r.health === 'Critical') {
      alerts.push({ id: `alert-rel-${r.releaseId}`, severity: 'critical', title: `Release ${r.releaseId} is critical`, message: `Completion: ${r.completionRate.toFixed(0)}%, ${r.overdueTasks} overdue, ${r.highRiskTasks} high-risk`, source: r.releaseId, timestamp: now });
    } else if (r.health === 'At Risk') {
      alerts.push({ id: `alert-rel-${r.releaseId}`, severity: 'warning', title: `Release ${r.releaseId} is at risk`, message: `Completion: ${r.completionRate.toFixed(0)}%, ${r.overdueTasks} overdue tasks`, source: r.releaseId, timestamp: now });
    }
  }
  const highEffortLow = features.filter((f) => f.devEffort > 5 && f.businessValue < 6);
  for (const f of highEffortLow) {
    alerts.push({ id: `alert-feat-${f.id}`, severity: 'warning', title: `Low-value feature: ${f.name}`, message: `High effort (${f.devEffort}) but below-average value (${f.businessValue.toFixed(1)}). Consider deferring.`, source: f.releaseId ?? 'N/A', timestamp: now });
  }
  // Sort alerts by severity (critical first)
  const severityOrder = { critical: 0, warning: 1, info: 2 };
  alerts.sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]);

  const completedTasks = tasks.filter((t) => /complete|done|closed|resolved/i.test(t.status)).length;
  const overdueTasks = tasks.filter((t) => t.daysOverdue > 0).length;
  const highRiskTasks = tasks.filter((t) => t.riskLevel === 'High').length;
  const openTasks = tasks.length - completedTasks;
  const highRiskReleases = releases.filter((r) => r.health === 'Critical').length;
  const totalDemand = features.reduce((s, f) => s + f.customerDemand, 0);

  const kpis: KpiSummary = {
    totalFeatures: features.length,
    totalTasks: tasks.length,
    avgWsJf: features.length > 0 ? features.reduce((s, f) => s + f.wsjfScore, 0) / features.length : 0,
    highPriorityCount: features.filter((f) => f.priorityLabel === 'Critical' || f.priorityLabel === 'High').length,
    overdueTasks,
    highRiskTasks,
    completionRate: tasks.length > 0 ? (completedTasks / tasks.length) * 100 : 0,
    highRiskReleases,
    totalReleases: releases.length,
    openTasks,
    totalDemand,
  };

  const recommendations = generateRecommendations(kpis, features, tasks, releases, dataset);

  return {
    kpis,
    features,
    tasks,
    releases,
    alerts,
    priorityDistribution,
    valueEffortScatter,
    riskDistribution,
    statusDistribution,
    demandTrend,
    releaseComparison,
    recommendations,
    summary: {
      processedRows: dataset.validRowCount,
      skippedRows: dataset.invalidRowCount,
      supportedAnalyses: dataset.supportedAnalyses,
      missingAnalyses: dataset.unsupportedAnalyses.map((u) => u.analysis),
    },
  };
}

function generateRecommendations(
  kpis: KpiSummary,
  features: FeatureRow[],
  tasks: TaskRow[],
  releases: ReleaseHealth[],
  dataset: AnalysisDataset
): Recommendation[] {
  const recs: Recommendation[] = [];

  if (features.length > 0) {
    const top = features.slice(0, 3);
    recs.push({
      id: 'rec-top-features',
      title: `Prioritize top ${top.length} features by WSJF score`,
      description: `Features "${top.map((f) => f.name).join('", "')}" have the highest weighted shortest job first scores. Allocate resources here first for maximum value delivery.`,
      severity: 'info',
      metric: `Avg WSJF: ${kpis.avgWsJf.toFixed(1)}`,
    });
  }

  if (kpis.overdueTasks > 0) {
    recs.push({
      id: 'rec-overdue',
      title: `${kpis.overdueTasks} task${kpis.overdueTasks > 1 ? 's are' : ' is'} overdue`,
      description: 'Review overdue tasks and either adjust planned dates or reallocate resources. Overdue tasks increase delivery risk and erode stakeholder confidence.',
      severity: kpis.overdueTasks > 3 ? 'critical' : 'warning',
      metric: `${kpis.overdueTasks} overdue`,
    });
  }

  if (kpis.highRiskTasks > 0) {
    recs.push({
      id: 'rec-high-risk',
      title: `${kpis.highRiskTasks} high-risk task${kpis.highRiskTasks > 1 ? 's' : ''} need attention`,
      description: 'High-risk tasks have significant schedule slippage. Consider breaking them down, reassigning, or escalating to remove blockers.',
      severity: 'critical',
      metric: `${kpis.highRiskTasks} high-risk`,
    });
  }

  if (kpis.highRiskReleases > 0) {
    recs.push({
      id: 'rec-high-risk-releases',
      title: `${kpis.highRiskReleases} release${kpis.highRiskReleases > 1 ? 's' : ''} in critical state`,
      description: releases.filter((r) => r.health === 'Critical').map((r) => `${r.releaseId} (${r.completionRate.toFixed(0)}% complete)`).join(', '),
      severity: 'critical',
      metric: `${kpis.highRiskReleases} critical`,
    });
  }

  if (kpis.completionRate < 50 && kpis.totalTasks > 0) {
    recs.push({
      id: 'rec-completion',
      title: 'Task completion rate is below 50%',
      description: `Current completion rate is ${kpis.completionRate.toFixed(0)}%. Evaluate whether scope is too broad or if the team needs additional capacity.`,
      severity: 'warning',
      metric: `${kpis.completionRate.toFixed(0)}% complete`,
    });
  }

  const highEffortLowValue = features.filter((f) => f.devEffort > 5 && f.businessValue < 6);
  if (highEffortLowValue.length > 0) {
    recs.push({
      id: 'rec-low-value-high-effort',
      title: `${highEffortLowValue.length} high-effort, low-value feature${highEffortLowValue.length > 1 ? 's' : ''} detected`,
      description: `Consider deferring: ${highEffortLowValue.map((f) => f.name).join(', ')}. These features require significant effort but deliver below-average business value.`,
      severity: 'warning',
      metric: `${highEffortLowValue.length} features`,
    });
  }

  if (dataset.unsupportedAnalyses.length > 0) {
    for (const u of dataset.unsupportedAnalyses) {
      recs.push({
        id: `rec-unsupported-${u.analysis}`,
        title: `"${u.analysis}" analysis unavailable`,
        description: `${u.reason} Map the required columns in the Data Workspace to enable this analysis.`,
        severity: 'warning',
        metric: 'Missing columns',
      });
    }
  }

  if (recs.length === 0) {
    recs.push({
      id: 'rec-all-good',
      title: 'All metrics within healthy range',
      description: 'No critical issues detected in the current dataset. Continue monitoring and re-run analysis after updates.',
      severity: 'info',
      metric: 'No issues',
    });
  }

  return recs;
}

export function validateDataset(dataset: UploadedDataset, mappings: ColumnMapping): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const mappedFields = Object.values(mappings).filter(Boolean) as SemanticField[];

  if (mappedFields.length === 0) {
    issues.push({
      type: 'error',
      message: 'No columns have been mapped to analytics fields. At least one mapping is required for analysis.',
    });
  }

  const duplicates = mappedFields.filter((f, i) => mappedFields.indexOf(f) !== i);
  if (duplicates.length > 0) {
    issues.push({
      type: 'error',
      message: `Duplicate field mapping detected: ${duplicates.join(', ')}. Each field should map to only one column.`,
    });
  }

  return issues;
}
