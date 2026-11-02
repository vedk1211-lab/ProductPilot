export type ColumnType = 'number' | 'date' | 'string' | 'boolean';

export type SemanticField =
  | 'featureId'
  | 'featureName'
  | 'customerDemand'
  | 'businessValue'
  | 'urgency'
  | 'strategicAlignment'
  | 'devEffort'
  | 'taskId'
  | 'projectId'
  | 'taskStatus'
  | 'plannedDate'
  | 'actualDate'
  | 'releaseId'
  | 'eventTimestamp'
  | 'eventIndicator';

export interface ColumnSchema {
  name: string;
  type: ColumnType;
  semanticField: SemanticField | null;
  missingCount: number;
  uniqueCount: number;
  sampleValues: string[];
}

export interface UploadedDataset {
  id: string;
  fileName: string;
  fileSize: number;
  rawHeaders: string[];
  rawRows: string[][];
  columns: ColumnSchema[];
  rowCount: number;
  columnCount: number;
  uploadedAt: number;
}

export interface ColumnMapping {
  [columnName: string]: SemanticField;
}

export interface AnalysisDataset {
  source: 'sample' | 'uploaded';
  rowCount: number;
  validRowCount: number;
  invalidRowCount: number;
  columns: ColumnSchema[];
  rows: Record<string, string | number | boolean | null>[];
  mappings: ColumnMapping;
  supportedAnalyses: string[];
  unsupportedAnalyses: { analysis: string; reason: string; requiredFields: SemanticField[] }[];
  computedAt: number;
}

export interface FeatureRow {
  id: string;
  name: string;
  customerDemand: number;
  businessValue: number;
  urgency: number;
  strategicAlignment: number;
  devEffort: number;
  wsjfScore: number;
  priorityRank: number;
  priorityLabel: 'Critical' | 'High' | 'Medium' | 'Low';
  releaseId: string | null;
  taskId: string | null;
}

export interface TaskRow {
  id: string;
  projectId: string;
  status: string;
  plannedDate: string | null;
  actualDate: string | null;
  daysOverdue: number;
  riskLevel: 'High' | 'Medium' | 'Low' | 'N/A';
  riskScore: number;
  riskReasons: string[];
  releaseId: string | null;
}

export interface KpiSummary {
  totalFeatures: number;
  totalTasks: number;
  avgWsJf: number;
  highPriorityCount: number;
  overdueTasks: number;
  highRiskTasks: number;
  completionRate: number;
  highRiskReleases: number;
  totalReleases: number;
  openTasks: number;
  totalDemand: number;
}

export interface ChartData {
  label: string;
  value: number;
  color?: string;
}

export interface TrendPoint {
  label: string;
  value: number;
}

export interface ReleaseHealth {
  releaseId: string;
  totalTasks: number;
  completedTasks: number;
  overdueTasks: number;
  highRiskTasks: number;
  completionRate: number;
  riskScore: number;
  health: 'Healthy' | 'At Risk' | 'Critical';
}

export interface AlertItem {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  title: string;
  message: string;
  source: string;
  timestamp: number;
}

export interface ScoringWeights {
  businessValue: number;
  urgency: number;
  strategicAlignment: number;
  customerDemand: number;
  devEffort: number;
}

export interface AnalysisResult {
  kpis: KpiSummary;
  features: FeatureRow[];
  tasks: TaskRow[];
  releases: ReleaseHealth[];
  alerts: AlertItem[];
  priorityDistribution: ChartData[];
  valueEffortScatter: { label: string; x: number; y: number; size: number }[];
  riskDistribution: ChartData[];
  statusDistribution: ChartData[];
  demandTrend: TrendPoint[];
  releaseComparison: ChartData[];
  recommendations: Recommendation[];
  summary: {
    processedRows: number;
    skippedRows: number;
    supportedAnalyses: string[];
    missingAnalyses: string[];
  };
}

export interface Recommendation {
  id: string;
  title: string;
  description: string;
  severity: 'info' | 'warning' | 'critical';
  metric: string;
}

export type DataSource = 'sample' | 'uploaded';

export interface ValidationIssue {
  type: 'error' | 'warning';
  message: string;
  columnName?: string;
}

export interface BloomFilterState {
  bitArray: boolean[];
  size: number;
  hashCount: number;
  insertedItems: string[];
  falsePositiveRate: number;
}

export interface DgimBucket {
  timestamp: number;
  size: number;
}

export interface DgimState {
  buckets: DgimBucket[];
  windowSize: number;
  currentTimestamp: number;
  approximateCount: number;
  exactCount: number;
  errorRate: number;
}
