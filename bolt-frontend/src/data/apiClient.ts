import type { AnalysisDataset, AnalysisResult, UploadedDataset, ColumnMapping } from './types';
import { buildAnalysisDataset, runAnalysis } from './analysis';

/**
 * ProductPilot Analysis API Client
 *
 * This layer provides a unified interface for running analyses. When a Python/PySpark
 * backend is available, set the ANALYSIS_API_URL environment variable and the client
 * will route requests to that backend. Otherwise it falls back to a clearly-labelled
 * local demo mode that performs genuine client-side calculations.
 *
 * The local mode keeps all data in browser memory — nothing is transmitted externally.
 */

const API_URL = (import.meta.env.VITE_ANALYSIS_API_URL as string | undefined)?.trim() || null;

export interface AnalysisRequest {
  dataset: UploadedDataset;
  mappings: ColumnMapping;
}

export interface AnalysisResponse {
  result: AnalysisResult;
  analysisDataset: AnalysisDataset;
  mode: 'backend' | 'local';
  backendName?: string;
}

export async function fetchBackendDataset(): Promise<AnalysisResponse | null> {
  if (API_URL) {
    try {
      const resp = await fetch(`${API_URL}/api/dataset`);
      if (resp.ok) {
        const data = await resp.json();
        return {
          result: data.result,
          analysisDataset: data.analysisDataset,
          mode: 'backend',
          backendName: data.backendName ?? 'PySpark Analytics Engine',
        };
      }
    } catch (err) {
      console.warn('Failed to fetch backend dataset, falling back to local sample:', err);
    }
  }
  return null;
}

export async function fetchPipelineStatus(): Promise<any | null> {
  if (API_URL) {
    try {
      const resp = await fetch(`${API_URL}/api/pipeline/status`);
      if (resp.ok) {
        return await resp.json();
      }
    } catch (err) {
      console.warn('Failed to fetch pipeline status:', err);
    }
  }
  return null;
}

export async function runAnalysisViaApi(req: AnalysisRequest): Promise<AnalysisResponse> {
  if (API_URL) {
    try {
      const resp = await fetch(`${API_URL}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          headers: req.dataset.rawHeaders,
          rows: req.dataset.rawRows,
          mappings: req.mappings,
          fileName: req.dataset.fileName,
        }),
      });
      if (!resp.ok) {
        throw new Error(`Backend returned ${resp.status}: ${resp.statusText}`);
      }
      const data = await resp.json();
      return {
        result: data.result,
        analysisDataset: data.analysisDataset,
        mode: 'backend',
        backendName: data.backendName ?? 'PySpark Analysis Service',
      };
    } catch (err) {
      console.warn('Backend analysis failed, falling back to local mode:', err);
    }
  }

  // Local demo mode — genuine client-side calculations
  const analysisDataset = buildAnalysisDataset(req.dataset, req.mappings);
  const result = runAnalysis(analysisDataset);

  return {
    result,
    analysisDataset,
    mode: 'local',
  };
}

export function getAnalysisMode(): 'backend' | 'local' {
  return API_URL ? 'backend' : 'local';
}

export function getBackendName(): string | null {
  return API_URL ? 'PySpark Analysis Service' : null;
}
