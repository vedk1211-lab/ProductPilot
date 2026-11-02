import { useState, useRef, useCallback, useMemo } from 'react';
import {
  Upload, Database, FileText, CheckCircle2, AlertTriangle, XCircle,
  Trash2, Play, ChevronLeft, ChevronRight, Info, FileUp, Loader2, RefreshCw,
} from 'lucide-react';
import { useData } from '@/context/useData';
import { createUploadedDataset, detectIssues, formatFileSize, MAX_FILE_SIZE } from '@/data/csvParser';
import { FIELD_LABELS, FIELD_DESCRIPTIONS, autoMapColumns } from '@/data/sampleData';
import { validateDataset } from '@/data/analysis';
import { Panel, PanelHeader } from '@/components/Panel';
import type { DataSource, SemanticField, ValidationIssue, ColumnMapping } from '@/data/types';

const ALL_FIELDS: SemanticField[] = [
  'featureId', 'featureName', 'customerDemand', 'businessValue', 'urgency',
  'strategicAlignment', 'devEffort', 'taskId', 'projectId', 'taskStatus',
  'plannedDate', 'actualDate', 'releaseId', 'eventTimestamp', 'eventIndicator',
];

const PREVIEW_PAGE_SIZE = 10;

export function DataWorkspacePage() {
  const {
    dataSource, uploadedDataset, columnMappings, validationIssues,
    isAnalyzing, lastAnalysisSummary, setDataSource, setUploadedDataset,
    updateColumnMappings, setValidationIssues, runAnalysisFlow, clearUpload, removeUploadedDataset,
  } = useData();

  const [dragOver, setDragOver] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadWarnings, setUploadWarnings] = useState<ValidationIssue[]>([]);
  const [previewPage, setPreviewPage] = useState(0);
  const [confirmRemove, setConfirmRemove] = useState(false);
  const [analysisSuccess, setAnalysisSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(async (file: File) => {
    setUploadError(null);
    setUploadWarnings([]);
    setAnalysisSuccess(false);
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setUploadError('Only CSV files are accepted. Please upload a file with a .csv extension.');
      return;
    }
    if (file.size > MAX_FILE_SIZE) {
      setUploadError(`File is too large (${formatFileSize(file.size)}). Maximum allowed size is ${formatFileSize(MAX_FILE_SIZE)}.`);
      return;
    }
    if (file.size === 0) {
      setUploadError('The file is empty. Please select a valid CSV file with data.');
      return;
    }
    try {
      const text = await file.text();
      const { dataset, issues } = createUploadedDataset(file.name, file.size, text);
      if (!dataset) {
        setUploadError(issues.find((i) => i.type === 'error')?.message ?? 'Failed to parse the CSV file.');
        return;
      }
      setUploadedDataset(dataset);
      setDataSource('uploaded');
      setPreviewPage(0);
      setUploadWarnings(detectIssues(dataset));
    } catch (err) {
      setUploadError(err instanceof Error ? `Failed to read the file: ${err.message}` : 'Failed to read the file. It may be corrupted or use an unsupported encoding.');
    }
  }, [setUploadedDataset, setDataSource]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const handleBrowse = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = '';
  }, [handleFile]);

  const handleMappingChange = useCallback((columnName: string, field: SemanticField | '') => {
    const newMappings = { ...columnMappings };
    if (field === '') delete newMappings[columnName];
    else newMappings[columnName] = field;
    updateColumnMappings(newMappings);
    setAnalysisSuccess(false);
  }, [columnMappings, updateColumnMappings]);

  const handleAutoMap = useCallback(() => {
    if (!uploadedDataset) return;
    const auto = autoMapColumns(uploadedDataset.rawHeaders);
    const newMappings: ColumnMapping = {};
    for (const [col, field] of Object.entries(auto)) {
      if (field) newMappings[col] = field;
    }
    updateColumnMappings(newMappings);
    setAnalysisSuccess(false);
  }, [uploadedDataset, updateColumnMappings]);

  const handleRunAnalysis = useCallback(async () => {
    setAnalysisSuccess(false);
    if (uploadedDataset) {
      const issues = validateDataset(uploadedDataset, columnMappings);
      setValidationIssues(issues);
      if (issues.some((i) => i.type === 'error')) return;
    }
    await runAnalysisFlow();
    setAnalysisSuccess(true);
  }, [uploadedDataset, columnMappings, setValidationIssues, runAnalysisFlow]);

  const handleClearUpload = useCallback(() => {
    clearUpload();
    setUploadError(null);
    setUploadWarnings([]);
    setAnalysisSuccess(false);
    setPreviewPage(0);
  }, [clearUpload]);

  const handleRemoveDataset = useCallback(() => {
    if (!confirmRemove) { setConfirmRemove(true); return; }
    removeUploadedDataset();
    setConfirmRemove(false);
    setUploadError(null);
    setUploadWarnings([]);
    setAnalysisSuccess(false);
    setPreviewPage(0);
  }, [confirmRemove, removeUploadedDataset]);

  const handleSwitchSource = useCallback((source: DataSource) => {
    if (source === dataSource) return;
    setDataSource(source);
    setAnalysisSuccess(false);
    if (source === 'sample') { setUploadError(null); setUploadWarnings([]); }
  }, [dataSource, setDataSource]);

  const previewData = useMemo(() => {
    if (!uploadedDataset) return { headers: [], rows: [], totalPages: 0, currentPage: 0 };
    const start = previewPage * PREVIEW_PAGE_SIZE;
    return {
      headers: uploadedDataset.rawHeaders,
      rows: uploadedDataset.rawRows.slice(start, start + PREVIEW_PAGE_SIZE),
      totalPages: Math.ceil(uploadedDataset.rowCount / PREVIEW_PAGE_SIZE),
      currentPage: previewPage,
    };
  }, [uploadedDataset, previewPage]);

  const mappedFields = useMemo(() => Object.values(columnMappings).filter(Boolean) as SemanticField[], [columnMappings]);
  const allIssues = useMemo(() => [...uploadWarnings, ...validationIssues], [uploadWarnings, validationIssues]);
  const errors = allIssues.filter((i) => i.type === 'error');
  const warnings = allIssues.filter((i) => i.type === 'warning');

  return (
    <div className="p-5 space-y-4 animate-fade-in">
      {/* Data Source Selector */}
      <Panel>
        <PanelHeader title="Data Source" subtitle="Select which dataset to use for analysis" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <ModeSelectorCard
            active={dataSource === 'sample'}
            onClick={() => handleSwitchSource('sample')}
            icon={<Database className="w-4 h-4" />}
            title="Sample Dataset"
            description="Pre-loaded product data with 20 features and tasks for exploration."
            badge="Default"
          />
          <ModeSelectorCard
            active={dataSource === 'uploaded'}
            onClick={() => handleSwitchSource('uploaded')}
            icon={<FileUp className="w-4 h-4" />}
            title="My Dataset"
            description="Upload your own CSV file with product, feature, or task data."
            badge={uploadedDataset ? 'Loaded' : 'Empty'}
            disabled={!uploadedDataset}
          />
        </div>
      </Panel>

      {/* Upload Area */}
      {!uploadedDataset && (
        <Panel>
          <PanelHeader title="Upload CSV File" subtitle="Drag and drop or browse. Data stays in your browser." />
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={`relative border-2 border-dashed rounded-lg transition-all duration-200 ${
              dragOver ? 'border-teal-400 bg-teal-50/50 scale-[1.01]' : 'border-slate-300 bg-slate-50/30 hover:border-slate-400'
            }`}
          >
            <input ref={fileInputRef} type="file" accept=".csv,text/csv" onChange={handleBrowse} className="hidden" />
            <div className="flex flex-col items-center justify-center py-10 px-6 text-center">
              <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-3 transition-colors ${dragOver ? 'bg-teal-100' : 'bg-slate-100'}`}>
                <Upload className={`w-6 h-6 ${dragOver ? 'text-teal-500' : 'text-slate-400'}`} />
              </div>
              <p className="text-sm font-medium text-slate-700 mb-1">{dragOver ? 'Drop your CSV file here' : 'Drag and drop your CSV file'}</p>
              <p className="text-xs text-slate-400 mb-3">or</p>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-3.5 py-1.5 bg-navy-600 text-white text-xs font-medium rounded-lg hover:bg-navy-700 transition-colors"
              >
                Browse Files
              </button>
              <p className="text-[11px] text-slate-400 mt-3">CSV only · Max {formatFileSize(MAX_FILE_SIZE)} · Processed locally</p>
            </div>
          </div>
          {uploadError && (
            <div className="mt-3 flex items-start gap-2.5 p-2.5 bg-red-50 border border-red-200 rounded-lg animate-fade-in">
              <XCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
              <p className="text-xs text-red-600">{uploadError}</p>
            </div>
          )}
        </Panel>
      )}

      {/* Uploaded Dataset */}
      {uploadedDataset && (
        <>
          {/* File Info */}
          <Panel>
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-10 h-10 rounded-lg bg-teal-50 flex items-center justify-center shrink-0">
                  <FileText className="w-5 h-5 text-teal-600" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-navy-800 truncate">{uploadedDataset.fileName}</p>
                  <div className="flex items-center gap-3 text-xs text-slate-500 mt-0.5">
                    <span>{formatFileSize(uploadedDataset.fileSize)}</span>
                    <span>{uploadedDataset.rowCount} rows</span>
                    <span>{uploadedDataset.columnCount} columns</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={handleClearUpload} className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-slate-600 bg-slate-50 border border-slate-200 rounded-lg hover:bg-slate-100 transition-colors">
                  <RefreshCw className="w-3.5 h-3.5" /> Clear
                </button>
                <button
                  onClick={handleRemoveDataset}
                  className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                    confirmRemove ? 'bg-red-600 text-white hover:bg-red-700' : 'text-red-600 bg-red-50 border border-red-200 hover:bg-red-100'
                  }`}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  {confirmRemove ? 'Confirm' : 'Remove'}
                </button>
              </div>
            </div>
            {confirmRemove && (
              <p className="text-xs text-red-600 mt-2 animate-fade-in">Removing the dataset will switch back to Sample Dataset. Click "Confirm" to proceed.</p>
            )}
          </Panel>

          {/* Validation Summary */}
          <Panel>
            <PanelHeader title="Data Validation Summary" />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 mb-3">
              <ValidationStat label="Total Rows" value={uploadedDataset.rowCount} icon={<FileText className="w-3.5 h-3.5" />} color="navy" />
              <ValidationStat label="Columns" value={uploadedDataset.columnCount} icon={<Database className="w-3.5 h-3.5" />} color="teal" />
              <ValidationStat label="Errors" value={errors.length} icon={<XCircle className="w-3.5 h-3.5" />} color={errors.length > 0 ? 'red' : 'green'} />
              <ValidationStat label="Warnings" value={warnings.length} icon={<AlertTriangle className="w-3.5 h-3.5" />} color={warnings.length > 0 ? 'amber' : 'green'} />
            </div>
            {errors.length > 0 && (
              <div className="space-y-1.5 mb-2">{errors.map((issue, i) => <IssueRow key={`err-${i}`} issue={issue} />)}</div>
            )}
            {warnings.length > 0 && (
              <div className="space-y-1.5">{warnings.map((issue, i) => <IssueRow key={`warn-${i}`} issue={issue} />)}</div>
            )}
            {errors.length === 0 && warnings.length === 0 && (
              <div className="flex items-center gap-2 text-xs text-emerald-600">
                <CheckCircle2 className="w-3.5 h-3.5" /> No validation issues detected. Data looks clean.
              </div>
            )}
          </Panel>

          {/* Column Mapping */}
          <Panel>
            <PanelHeader
              title="Column Mapping"
              subtitle="Map CSV columns to analytics fields"
              action={
                <button onClick={handleAutoMap} className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-teal-600 bg-teal-50 border border-teal-200 rounded-lg hover:bg-teal-100 transition-colors">
                  <RefreshCw className="w-3.5 h-3.5" /> Auto-Map
                </button>
              }
            />
            <div className="overflow-x-auto scrollbar-thin">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200">
                    <Th>CSV Column</Th>
                    <Th>Type</Th>
                    <Th align="right">Missing</Th>
                    <Th align="right">Unique</Th>
                    <Th>Map To</Th>
                  </tr>
                </thead>
                <tbody>
                  {uploadedDataset.columns.map((col) => (
                    <tr key={col.name} className="border-b border-slate-100 hover:bg-slate-50/40 transition-colors">
                      <td className="py-2 px-3 font-medium text-navy-700 text-xs">{col.name}</td>
                      <td className="py-2 px-3"><TypeBadge type={col.type} /></td>
                      <td className="py-2 px-3 text-right text-xs">{col.missingCount > 0 ? <span className="text-amber-600">{col.missingCount}</span> : <span className="text-slate-300">0</span>}</td>
                      <td className="py-2 px-3 text-right text-xs text-slate-500">{col.uniqueCount}</td>
                      <td className="py-2 px-3">
                        <select
                          value={columnMappings[col.name] ?? ''}
                          onChange={(e) => handleMappingChange(col.name, e.target.value as SemanticField | '')}
                          className="w-full max-w-[180px] px-2 py-1 text-xs border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-teal-400/30 focus:border-teal-400"
                        >
                          <option value="">— Unmapped —</option>
                          {ALL_FIELDS.map((f) => (
                            <option key={f} value={f} disabled={mappedFields.includes(f) && columnMappings[col.name] !== f}>
                              {FIELD_LABELS[f]}
                            </option>
                          ))}
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {mappedFields.length < ALL_FIELDS.length && (
              <div className="mt-3 p-2.5 bg-navy-50 border border-navy-100 rounded-lg flex items-start gap-2.5">
                <Info className="w-3.5 h-3.5 text-navy-500 shrink-0 mt-0.5" />
                <div className="text-xs">
                  <p className="font-medium text-navy-700">{ALL_FIELDS.length - mappedFields.length} field(s) unmapped</p>
                  <p className="text-navy-600/70 mt-0.5">Unmapped fields may cause some analyses to be unavailable. Map at least demand, value, and effort for feature prioritization.</p>
                </div>
              </div>
            )}
          </Panel>

          {/* Data Preview */}
          <Panel>
            <PanelHeader
              title="Original Data Preview"
              subtitle="Raw uploaded data — no transformations"
              action={previewData.totalPages > 1 ? (
                <div className="flex items-center gap-1.5">
                  <button onClick={() => setPreviewPage(Math.max(0, previewPage - 1))} disabled={previewPage === 0} className="p-1 rounded border border-slate-200 text-slate-500 disabled:opacity-30 hover:bg-slate-50 transition-colors">
                    <ChevronLeft className="w-3.5 h-3.5" />
                  </button>
                  <span className="text-[11px] text-slate-500">Page {previewData.currentPage + 1} of {previewData.totalPages}</span>
                  <button onClick={() => setPreviewPage(Math.min(previewData.totalPages - 1, previewPage + 1))} disabled={previewPage >= previewData.totalPages - 1} className="p-1 rounded border border-slate-200 text-slate-500 disabled:opacity-30 hover:bg-slate-50 transition-colors">
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              ) : undefined}
            />
            <div className="overflow-x-auto scrollbar-thin border border-slate-100 rounded-lg">
              <table className="w-full text-sm">
                <thead className="bg-slate-50/80">
                  <tr>
                    <th className="text-left py-2 px-2.5 font-medium text-slate-400 text-[10px] w-8">#</th>
                    {previewData.headers.map((h) => (
                      <th key={h} className="text-left py-2 px-2.5 font-medium text-slate-500 text-[10px] whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {previewData.rows.map((row, i) => (
                    <tr key={i} className="border-t border-slate-100 hover:bg-slate-50/30">
                      <td className="py-1.5 px-2.5 text-slate-400 text-[10px]">{previewData.currentPage * PREVIEW_PAGE_SIZE + i + 1}</td>
                      {previewData.headers.map((h, j) => {
                        const val = row[j] ?? '';
                        return <td key={h} className={`py-1.5 px-2.5 whitespace-nowrap text-xs ${val === '' ? 'text-slate-300 italic' : 'text-slate-600'}`}>{val === '' ? '—' : val}</td>;
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-[11px] text-slate-400 mt-2">Showing {previewData.rows.length} of {uploadedDataset.rowCount} rows</p>
          </Panel>

          {/* Run Analysis */}
          <Panel>
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div>
                <h3 className="text-sm font-semibold text-navy-800">Run Analysis</h3>
                <p className="text-xs text-slate-500 mt-0.5">Validate, apply mappings, and recalculate all dashboard metrics.</p>
              </div>
              <button
                onClick={handleRunAnalysis}
                disabled={isAnalyzing || errors.length > 0}
                className="flex items-center gap-2 px-5 py-2.5 bg-teal-600 text-white text-sm font-semibold rounded-lg hover:bg-teal-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {isAnalyzing ? (<><Loader2 className="w-4 h-4 animate-spin" /> Analyzing…</>) : (<><Play className="w-4 h-4" /> Run Analysis</>)}
              </button>
            </div>

            {analysisSuccess && lastAnalysisSummary && (
              <div className="mt-3 p-3 bg-emerald-50 border border-emerald-200 rounded-lg animate-fade-in">
                <div className="flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-xs font-semibold text-emerald-700">Analysis Complete</p>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-2">
                      <SummaryItem label="Processed" value={lastAnalysisSummary.processedRows} />
                      <SummaryItem label="Skipped" value={lastAnalysisSummary.skippedRows} />
                      <SummaryItem label="Supported" value={lastAnalysisSummary.supportedAnalyses.length} />
                      <SummaryItem label="Unavailable" value={lastAnalysisSummary.missingAnalyses.length} />
                    </div>
                    {lastAnalysisSummary.supportedAnalyses.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {lastAnalysisSummary.supportedAnalyses.map((a) => (
                          <span key={a} className="px-1.5 py-0.5 text-[10px] bg-emerald-100 text-emerald-700 rounded border border-emerald-200">
                            {a.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {errors.length > 0 && !isAnalyzing && (
              <div className="mt-3 p-2.5 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2.5">
                <AlertTriangle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
                <p className="text-xs text-red-600">Fix the validation errors above before running analysis. {errors.length} error(s) detected.</p>
              </div>
            )}
          </Panel>
        </>
      )}

      {/* Field Reference */}
      {!uploadedDataset && (
        <Panel>
          <PanelHeader title="Supported Analytics Fields" subtitle="Your CSV can contain any of these columns. Partial data is supported." />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
            {ALL_FIELDS.map((f) => (
              <div key={f} className="p-2.5 bg-slate-50/50 rounded-lg border border-slate-100">
                <p className="text-xs font-medium text-navy-700">{FIELD_LABELS[f]}</p>
                <p className="text-[11px] text-slate-400 mt-0.5">{FIELD_DESCRIPTIONS[f]}</p>
              </div>
            ))}
          </div>
        </Panel>
      )}
    </div>
  );
}

function ModeSelectorCard({ active, onClick, icon, title, description, badge, disabled }: {
  active: boolean; onClick: () => void; icon: React.ReactNode; title: string; description: string; badge: string; disabled?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`relative text-left p-3.5 rounded-lg border-2 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-teal-400/30 ${
        active ? 'border-teal-400 bg-teal-50/40' : 'border-slate-200 bg-white hover:border-slate-300'
      } ${disabled ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}
    >
      <div className="flex items-start gap-2.5">
        <div className={`w-8 h-8 rounded-md flex items-center justify-center shrink-0 ${active ? 'bg-teal-100 text-teal-600' : 'bg-slate-100 text-slate-400'}`}>
          {icon}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="text-xs font-semibold text-navy-800">{title}</p>
            <span className={`text-[9px] px-1.5 py-0.5 rounded font-medium ${active ? 'bg-teal-200 text-teal-700' : 'bg-slate-100 text-slate-400'}`}>{badge}</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">{description}</p>
        </div>
        {active && <CheckCircle2 className="w-4 h-4 text-teal-500 shrink-0" />}
      </div>
    </button>
  );
}

function ValidationStat({ label, value, icon, color }: { label: string; value: number | string; icon: React.ReactNode; color: 'navy' | 'teal' | 'red' | 'green' | 'amber' }) {
  const styles = {
    navy: 'bg-navy-50 text-navy-600', teal: 'bg-teal-50 text-teal-600', red: 'bg-red-50 text-red-600',
    green: 'bg-emerald-50 text-emerald-600', amber: 'bg-amber-50 text-amber-600',
  };
  return (
    <div className={`flex items-center gap-2.5 p-2.5 rounded-lg ${styles[color]}`}>
      <div className="shrink-0">{icon}</div>
      <div>
        <p className="text-base font-bold leading-tight">{value}</p>
        <p className="text-[10px] opacity-80">{label}</p>
      </div>
    </div>
  );
}

function IssueRow({ issue }: { issue: ValidationIssue }) {
  const isError = issue.type === 'error';
  const Icon = isError ? XCircle : AlertTriangle;
  return (
    <div className={`flex items-start gap-2 p-2 rounded-lg ${isError ? 'bg-red-50 border border-red-100' : 'bg-amber-50 border border-amber-100'}`}>
      <Icon className={`w-3.5 h-3.5 shrink-0 mt-0.5 ${isError ? 'text-red-500' : 'text-amber-500'}`} />
      <p className={`text-xs ${isError ? 'text-red-700' : 'text-amber-700'}`}>{issue.message}</p>
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

function SummaryItem({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white/60 rounded p-1.5">
      <p className="text-sm font-bold text-emerald-700 leading-tight">{value}</p>
      <p className="text-[10px] text-emerald-600/70">{label}</p>
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
