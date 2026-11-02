import {
  createContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from 'react';
import type {
  AnalysisDataset,
  AnalysisResult,
  ColumnMapping,
  DataSource,
  UploadedDataset,
  ValidationIssue,
} from '@/data/types';
import {
  getSampleAnalysisDataset,
  runAnalysis,
  validateDataset,
} from '@/data/analysis';
import {
  runAnalysisViaApi,
  getAnalysisMode,
  getBackendName,
  fetchBackendDataset,
} from '@/data/apiClient';

export interface DataContextValue {
  dataSource: DataSource;
  uploadedDataset: UploadedDataset | null;
  analysisDataset: AnalysisDataset | null;
  analysisResult: AnalysisResult | null;
  columnMappings: ColumnMapping;
  validationIssues: ValidationIssue[];
  isAnalyzing: boolean;
  analysisMode: 'backend' | 'local';
  backendName: string | null;
  lastAnalysisSummary: AnalysisResult['summary'] | null;

  setDataSource: (source: DataSource) => void;
  setUploadedDataset: (dataset: UploadedDataset | null) => void;
  updateColumnMappings: (mappings: ColumnMapping) => void;
  setValidationIssues: (issues: ValidationIssue[]) => void;
  runAnalysisFlow: () => Promise<void>;
  clearUpload: () => void;
  removeUploadedDataset: () => void;
}

export const DataContext = createContext<DataContextValue | null>(null);

export function DataProvider({ children }: { children: ReactNode }) {
  const [dataSource, setDataSource] = useState<DataSource>('sample');
  const [uploadedDataset, setUploadedDataset] = useState<UploadedDataset | null>(null);
  const [columnMappings, setColumnMappings] = useState<ColumnMapping>({});
  const [validationIssues, setValidationIssues] = useState<ValidationIssue[]>([]);
  const [analysisDataset, setAnalysisDataset] = useState<AnalysisDataset | null>(() => getSampleAnalysisDataset());
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(() => runAnalysis(getSampleAnalysisDataset()));
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [lastAnalysisSummary, setLastAnalysisSummary] = useState<AnalysisResult['summary'] | null>(null);

  const analysisMode = getAnalysisMode();
  const backendName = getBackendName();

  // Load real Big Data from backend on startup if available
  useEffect(() => {
    if (analysisMode === 'backend') {
      setIsAnalyzing(true);
      fetchBackendDataset()
        .then((resp) => {
          if (resp) {
            setAnalysisDataset(resp.analysisDataset);
            setAnalysisResult(resp.result);
          }
        })
        .catch((err) => console.warn('Failed to load initial backend dataset:', err))
        .finally(() => setIsAnalyzing(false));
    }
  }, [analysisMode]);

  const handleSetDataSource = useCallback(
    async (source: DataSource) => {
      setDataSource(source);
      if (source === 'sample') {
        if (analysisMode === 'backend') {
          setIsAnalyzing(true);
          try {
            const resp = await fetchBackendDataset();
            if (resp) {
              setAnalysisDataset(resp.analysisDataset);
              setAnalysisResult(resp.result);
              setLastAnalysisSummary(null);
              return;
            }
          } catch (err) {
            console.warn('Backend fetch failed, falling back to local demo:', err);
          } finally {
            setIsAnalyzing(false);
          }
        }
        const sample = getSampleAnalysisDataset();
        setAnalysisDataset(sample);
        setAnalysisResult(runAnalysis(sample));
        setLastAnalysisSummary(null);
      }
    },
    [analysisMode]
  );

  const handleSetUploadedDataset = useCallback((dataset: UploadedDataset | null) => {
    setUploadedDataset(dataset);
    if (dataset) {
      const initialMappings: ColumnMapping = {};
      for (const col of dataset.columns) {
        if (col.semanticField) {
          initialMappings[col.name] = col.semanticField;
        }
      }
      setColumnMappings(initialMappings);
    } else {
      setColumnMappings({});
      setValidationIssues([]);
    }
  }, []);

  const updateColumnMappings = useCallback((mappings: ColumnMapping) => {
    setColumnMappings(mappings);
  }, []);

  const setValidationIssuesCb = useCallback((issues: ValidationIssue[]) => {
    setValidationIssues(issues);
  }, []);

  const runAnalysisFlow = useCallback(async () => {
    if (dataSource === 'sample') {
      if (analysisMode === 'backend') {
        setIsAnalyzing(true);
        try {
          const resp = await fetchBackendDataset();
          if (resp) {
            setAnalysisDataset(resp.analysisDataset);
            setAnalysisResult(resp.result);
            setLastAnalysisSummary(resp.result.summary);
            return;
          }
        } catch (err) {
          console.warn('Backend fetch failed:', err);
        } finally {
          setIsAnalyzing(false);
        }
      }
      const sample = getSampleAnalysisDataset();
      setAnalysisDataset(sample);
      const result = runAnalysis(sample);
      setAnalysisResult(result);
      setLastAnalysisSummary(result.summary);
      return;
    }

    if (!uploadedDataset) return;

    const issues = validateDataset(uploadedDataset, columnMappings);
    setValidationIssues(issues);
    if (issues.some((i) => i.type === 'error')) return;

    setIsAnalyzing(true);
    try {
      const { result, analysisDataset: ad, mode, backendName: bn } = await runAnalysisViaApi({
        dataset: uploadedDataset,
        mappings: columnMappings,
      });
      setAnalysisDataset(ad);
      setAnalysisResult(result);
      setLastAnalysisSummary(result.summary);
      void mode;
      void bn;
    } finally {
      setIsAnalyzing(false);
    }
  }, [dataSource, uploadedDataset, columnMappings, analysisMode]);

  const clearUpload = useCallback(() => {
    setUploadedDataset(null);
    setColumnMappings({});
    setValidationIssues([]);
    setLastAnalysisSummary(null);
  }, []);

  const removeUploadedDataset = useCallback(() => {
    setUploadedDataset(null);
    setColumnMappings({});
    setValidationIssues([]);
    setLastAnalysisSummary(null);
    handleSetDataSource('sample');
  }, [handleSetDataSource]);

  const value: DataContextValue = {
    dataSource,
    uploadedDataset,
    analysisDataset,
    analysisResult,
    columnMappings,
    validationIssues,
    isAnalyzing,
    analysisMode,
    backendName,
    lastAnalysisSummary,
    setDataSource: handleSetDataSource,
    setUploadedDataset: handleSetUploadedDataset,
    updateColumnMappings,
    setValidationIssues: setValidationIssuesCb,
    runAnalysisFlow,
    clearUpload,
    removeUploadedDataset,
  };

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
}
