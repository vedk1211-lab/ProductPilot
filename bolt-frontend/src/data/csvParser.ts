import type { ColumnSchema, UploadedDataset, ValidationIssue } from './types';
import { inferColumnType, autoMapColumns, FIELD_KEYWORDS } from './sampleData';

export interface CsvParseResult {
  headers: string[];
  rows: string[][];
  issues: ValidationIssue[];
}

export function parseCsv(text: string): CsvParseResult {
  const issues: ValidationIssue[] = [];
  const lines = splitCsvLines(text);

  if (lines.length === 0) {
    return { headers: [], rows: [], issues: [{ type: 'error', message: 'The file is empty or contains no readable data.' }] };
  }

  const headers = parseCsvLine(lines[0]);
  if (headers.length === 0) {
    return { headers: [], rows: [], issues: [{ type: 'error', message: 'No column headers found. Ensure the first row contains column names.' }] };
  }

  const seen = new Map<string, number>();
  for (const h of headers) {
    const key = h.toLowerCase().trim();
    seen.set(key, (seen.get(key) ?? 0) + 1);
  }
  for (const [key, count] of seen) {
    if (count > 1) {
      issues.push({
        type: 'error',
        message: `Duplicate column name "${key}" detected (${count} occurrences). Column names must be unique.`,
      });
    }
  }

  const rows: string[][] = [];
  for (let i = 1; i < lines.length; i++) {
    if (lines[i].trim() === '') continue;
    const values = parseCsvLine(lines[i]);
    if (values.length === 1 && values[0] === '') continue;
    rows.push(values);
  }

  if (rows.length === 0) {
    issues.push({ type: 'warning', message: 'The CSV has headers but no data rows. Analysis cannot proceed without data.' });
  }

  return { headers, rows, issues };
}

function splitCsvLines(text: string): string[] {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ch === '"') {
      inQuotes = !inQuotes;
      current += ch;
    } else if ((ch === '\n' || ch === '\r') && !inQuotes) {
      if (ch === '\r' && text[i + 1] === '\n') i++;
      result.push(current);
      current = '';
    } else {
      current += ch;
    }
  }
  if (current !== '') result.push(current);
  return result;
}

function parseCsvLine(line: string): string[] {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (ch === ',' && !inQuotes) {
      result.push(current.trim());
      current = '';
    } else {
      current += ch;
    }
  }
  result.push(current.trim());
  return result;
}

export function buildColumnSchemas(headers: string[], rows: string[][]): ColumnSchema[] {
  return headers.map((header, colIdx) => {
    const values = rows.map((r) => r[colIdx] ?? '');
    const nonEmpty = values.filter((v) => v !== '' && v !== undefined);
    const missingCount = values.length - nonEmpty.length;
    const uniqueSet = new Set(nonEmpty);
    return {
      name: header,
      type: inferColumnType(nonEmpty),
      semanticField: autoMapColumns([header])[header] ?? null,
      missingCount,
      uniqueCount: uniqueSet.size,
      sampleValues: nonEmpty.slice(0, 5),
    };
  });
}

export function createUploadedDataset(fileName: string, fileSize: number, text: string): {
  dataset: UploadedDataset | null;
  issues: ValidationIssue[];
} {
  const { headers, rows, issues } = parseCsv(text);

  if (issues.some((i) => i.type === 'error')) {
    return { dataset: null, issues };
  }

  if (headers.length === 0) {
    return { dataset: null, issues: [{ type: 'error', message: 'No columns found in the CSV file.' }] };
  }

  const columns = buildColumnSchemas(headers, rows);

  return {
    dataset: {
      id: `upload-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      fileName,
      fileSize,
      rawHeaders: headers,
      rawRows: rows,
      columns,
      rowCount: rows.length,
      columnCount: headers.length,
      uploadedAt: Date.now(),
    },
    issues,
  };
}

export function detectIssues(dataset: UploadedDataset): ValidationIssue[] {
  const issues: ValidationIssue[] = [];

  const mappedFields = new Set(dataset.columns.filter((c) => c.semanticField).map((c) => c.semanticField));
  if (mappedFields.size === 0) {
    issues.push({
      type: 'warning',
      message: 'No columns could be automatically mapped to known analytics fields. Manual mapping is required.',
    });
  }

  for (const col of dataset.columns) {
    if (col.missingCount > 0 && col.missingCount / dataset.rowCount > 0.5) {
      issues.push({
        type: 'warning',
        message: `Column "${col.name}" has ${col.missingCount} missing values (${Math.round((col.missingCount / dataset.rowCount) * 100)}% of rows).`,
        columnName: col.name,
      });
    }
  }

  for (const col of dataset.columns) {
    if (col.semanticField) {
      const fieldDef = FIELD_KEYWORDS.find((f) => f.field === col.semanticField);
      if (fieldDef && fieldDef.preferredType !== col.type) {
        issues.push({
          type: 'warning',
          message: `Column "${col.name}" was detected as ${col.type} but the mapped field "${fieldDef.field}" expects ${fieldDef.preferredType}. Values will be converted.`,
          columnName: col.name,
        });
      }
    }
  }

  return issues;
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB
export const ACCEPTED_EXTENSIONS = ['.csv'];
