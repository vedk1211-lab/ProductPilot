import type { ColumnSchema, SemanticField } from './types';

export const SAMPLE_CSV_HEADERS = [
  'feature_id',
  'feature_name',
  'customer_demand',
  'business_value',
  'urgency',
  'strategic_alignment',
  'dev_effort',
  'task_id',
  'project_id',
  'task_status',
  'planned_date',
  'actual_date',
  'release_id',
];

export const SAMPLE_CSV_ROWS: string[][] = [
  ['F-001', 'Unified Dashboard Search', '45', '8.5', '9', '4', '5', 'T-1001', 'P-Atlas', 'In Progress', '2025-11-15', '', 'R-2025.4'],
  ['F-002', 'Mobile Push Notifications', '32', '7.2', '6', '5', '3', 'T-1002', 'P-Atlas', 'Completed', '2025-10-01', '2025-09-28', 'R-2025.3'],
  ['F-003', 'SSO with SAML 2.0', '18', '6.8', '7', '5', '8', 'T-1003', 'P-Atlas', 'In Progress', '2025-12-01', '', 'R-2025.4'],
  ['F-004', 'Audit Trail Export', '12', '5.5', '4', '4', '3', 'T-1004', 'P-Comply', 'Completed', '2025-09-15', '2025-09-14', 'R-2025.3'],
  ['F-005', 'Custom Report Builder', '38', '8.0', '8', '5', '7', 'T-1005', 'P-Atlas', 'Not Started', '2026-01-15', '', 'R-2026.1'],
  ['F-006', 'API Rate Limiting', '8', '6.0', '5', '4', '2', 'T-1006', 'P-Comply', 'Completed', '2025-08-20', '2025-08-18', 'R-2025.2'],
  ['F-007', 'Multi-language Support', '25', '7.5', '6', '5', '9', 'T-1007', 'P-Atlas', 'In Progress', '2026-02-01', '', 'R-2026.1'],
  ['F-008', 'Slack Integration', '41', '6.5', '7', '3', '4', 'T-1008', 'P-Connect', 'Not Started', '2025-12-15', '', 'R-2025.4'],
  ['F-009', 'Data Retention Policies', '6', '7.8', '9', '5', '5', 'T-1009', 'P-Comply', 'In Progress', '2025-11-30', '', 'R-2025.4'],
  ['F-010', 'Onboarding Wizard', '52', '8.2', '8', '5', '6', 'T-1010', 'P-Atlas', 'In Progress', '2025-11-20', '', 'R-2025.4'],
  ['F-011', 'Webhook Event Log', '14', '5.8', '5', '4', '3', 'T-1011', 'P-Connect', 'Completed', '2025-09-30', '2025-10-02', 'R-2025.3'],
  ['F-012', 'Role-based Access Control', '22', '8.5', '9', '5', '6', 'T-1012', 'P-Comply', 'In Progress', '2025-12-10', '', 'R-2025.4'],
  ['F-013', 'Performance Dashboard', '28', '7.0', '6', '4', '4', 'T-1013', 'P-Atlas', 'Not Started', '2026-01-10', '', 'R-2026.1'],
  ['F-014', 'Email Template Editor', '19', '5.0', '3', '3', '3', 'T-1014', 'P-Connect', 'Completed', '2025-07-15', '2025-07-14', 'R-2025.2'],
  ['F-015', 'Feature Flag System', '35', '7.2', '7', '5', '5', 'T-1015', 'P-Atlas', 'In Progress', '2025-11-25', '', 'R-2025.4'],
  ['F-016', 'Customer Feedback Widget', '48', '6.8', '8', '4', '4', 'T-1016', 'P-Connect', 'Not Started', '2025-12-20', '', 'R-2025.4'],
  ['F-017', 'Analytics Export API', '16', '7.5', '6', '5', '5', 'T-1017', 'P-Atlas', 'Completed', '2025-10-10', '2025-10-12', 'R-2025.3'],
  ['F-018', 'Two-factor Authentication', '20', '8.8', '9', '5', '4', 'T-1018', 'P-Comply', 'In Progress', '2025-11-05', '', 'R-2025.4'],
  ['F-019', 'Bulk Import Tool', '30', '6.0', '5', '3', '4', 'T-1019', 'P-Atlas', 'Not Started', '2026-02-15', '', 'R-2026.1'],
  ['F-020', 'Activity Timeline View', '26', '6.5', '5', '4', '3', 'T-1020', 'P-Atlas', 'In Progress', '2025-11-10', '', 'R-2025.4'],
];

export function getSampleColumnSchemas(): ColumnSchema[] {
  return SAMPLE_CSV_HEADERS.map((header) => {
    const values = SAMPLE_CSV_ROWS.map((r) => r[SAMPLE_CSV_HEADERS.indexOf(header)]);
    const nonEmpty = values.filter((v) => v !== '');
    const missingCount = values.length - nonEmpty.length;
    return {
      name: header,
      type: inferColumnType(nonEmpty),
      semanticField: FIELD_KEYWORDS.find((k) =>
        k.keywords.some((kw) => header.toLowerCase().includes(kw))
      )?.field ?? null,
      missingCount,
      uniqueCount: new Set(nonEmpty).size,
      sampleValues: nonEmpty.slice(0, 5),
    };
  });
}

export function inferColumnType(values: string[]): ColumnSchema['type'] {
  if (values.length === 0) return 'string';
  let numCount = 0;
  let dateCount = 0;
  let boolCount = 0;
  for (const v of values) {
    if (v === '' ) continue;
    if (!isNaN(Number(v)) && v.trim() !== '') numCount++;
    if (/^\d{4}-\d{2}-\d{2}/.test(v) || /^\d{1,2}\/\d{1,2}\/\d{2,4}/.test(v)) dateCount++;
    if (/^(true|false|yes|no)$/i.test(v)) boolCount++;
  }
  const total = values.filter((v) => v !== '').length;
  if (total === 0) return 'string';
  if (boolCount / total > 0.8) return 'boolean';
  if (dateCount / total > 0.7) return 'date';
  if (numCount / total > 0.7) return 'number';
  return 'string';
}

export const FIELD_KEYWORDS: { field: SemanticField; keywords: string[]; preferredType: ColumnSchema['type'] }[] = [
  { field: 'featureId', keywords: ['feature_id', 'featureid', 'feature id', 'feat_id'], preferredType: 'string' },
  { field: 'featureName', keywords: ['feature_name', 'featurename', 'feature name', 'feature', 'title', 'name'], preferredType: 'string' },
  { field: 'customerDemand', keywords: ['customer_demand', 'demand', 'request', 'requests', 'request_count', 'votes', 'customer_requests'], preferredType: 'number' },
  { field: 'businessValue', keywords: ['business_value', 'value', 'biz_value', 'roi', 'impact', 'benefit'], preferredType: 'number' },
  { field: 'urgency', keywords: ['urgency', 'urgent', 'priority', 'time_critical', 'deadline'], preferredType: 'number' },
  { field: 'strategicAlignment', keywords: ['strategic', 'alignment', 'strategy', 'strategic_alignment', 'strategic_score'], preferredType: 'number' },
  { field: 'devEffort', keywords: ['dev_effort', 'effort', 'estimate', 'story_points', 'complexity', 'work', 'dev_effort'], preferredType: 'number' },
  { field: 'taskId', keywords: ['task_id', 'taskid', 'task id', 'ticket_id', 'ticket', 'issue_id', 'jira_id'], preferredType: 'string' },
  { field: 'projectId', keywords: ['project_id', 'projectid', 'project id', 'project', 'epic_id', 'sprint_id'], preferredType: 'string' },
  { field: 'taskStatus', keywords: ['task_status', 'status', 'state', 'task_state', 'workflow_state'], preferredType: 'string' },
  { field: 'plannedDate', keywords: ['planned_date', 'planned', 'due_date', 'due', 'target_date', 'expected', 'planned_completion'], preferredType: 'date' },
  { field: 'actualDate', keywords: ['actual_date', 'actual', 'completed_date', 'completed', 'done_date', 'closed_date', 'finished'], preferredType: 'date' },
  { field: 'releaseId', keywords: ['release_id', 'releaseid', 'release id', 'release', 'version', 'milestone'], preferredType: 'string' },
  { field: 'eventTimestamp', keywords: ['event_timestamp', 'timestamp', 'event_time', 'event_date', 'time', 'created_at', 'updated_at', 'logged_at'], preferredType: 'date' },
  { field: 'eventIndicator', keywords: ['event_indicator', 'event', 'is_event', 'has_event', 'flag', 'triggered', 'binary_event'], preferredType: 'boolean' },
];

export const FIELD_LABELS: Record<SemanticField, string> = {
  featureId: 'Feature ID',
  featureName: 'Feature Name',
  customerDemand: 'Customer Demand',
  businessValue: 'Business Value',
  urgency: 'Urgency',
  strategicAlignment: 'Strategic Alignment',
  devEffort: 'Dev Effort',
  taskId: 'Task ID',
  projectId: 'Project ID',
  taskStatus: 'Task Status',
  plannedDate: 'Planned Completion Date',
  actualDate: 'Actual Completion Date',
  releaseId: 'Release ID',
  eventTimestamp: 'Event Timestamp',
  eventIndicator: 'Event Indicator',
};

export const FIELD_DESCRIPTIONS: Record<SemanticField, string> = {
  featureId: 'Unique identifier for each feature or item',
  featureName: 'Human-readable name of the feature',
  customerDemand: 'Number of customer requests or votes',
  businessValue: 'Quantified business impact or ROI (1–10 scale)',
  urgency: 'Time criticality score (1–10 scale)',
  strategicAlignment: 'How well the feature aligns with strategy (1–5 scale)',
  devEffort: 'Estimated development effort (story points or hours)',
  taskId: 'Unique task or ticket identifier',
  projectId: 'Project, epic, or sprint grouping',
  taskStatus: 'Current workflow status of the task',
  plannedDate: 'Planned or target completion date',
  actualDate: 'Actual completion date',
  releaseId: 'Release or version identifier',
  eventTimestamp: 'Timestamp of a logged event',
  eventIndicator: 'Binary flag indicating whether an event occurred',
};

export function autoMapColumns(columnNames: string[]): Record<string, SemanticField | null> {
  const mapping: Record<string, SemanticField | null> = {};
  const usedFields = new Set<SemanticField>();

  for (const col of columnNames) {
    const normalized = col.toLowerCase().trim();
    let bestMatch: SemanticField | null = null;
    let bestScore = 0;

    for (const kw of FIELD_KEYWORDS) {
      for (const keyword of kw.keywords) {
        if (normalized === keyword) {
          bestMatch = kw.field;
          bestScore = 100;
          break;
        }
        if (normalized.includes(keyword) && keyword.length > bestScore) {
          bestScore = keyword.length;
          bestMatch = kw.field;
        }
      }
      if (bestScore === 100) break;
    }

    if (bestMatch && !usedFields.has(bestMatch)) {
      mapping[col] = bestMatch;
      usedFields.add(bestMatch);
    } else {
      mapping[col] = null;
    }
  }

  return mapping;
}
