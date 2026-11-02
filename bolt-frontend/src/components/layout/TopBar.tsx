import { Database, CheckCircle2, Upload, Loader2 } from 'lucide-react';
import { useData } from '@/context/useData';
import type { PageId } from './Sidebar';

const PAGE_TITLES: Record<PageId, { title: string; subtitle: string }> = {
  dashboard: { title: 'Executive Overview', subtitle: 'Portfolio performance indicators and analytics summary' },
  features: { title: 'Feature Prioritization', subtitle: 'Configurable WSJF scoring with ranked feature backlog' },
  'task-risk': { title: 'Project Delivery Risks', subtitle: 'Schedule risk, release health, and overdue detection' },
  'bloom-filter': { title: 'Bloom Filter Laboratory', subtitle: 'Probabilistic membership testing with false-positive evaluation' },
  dgim: { title: 'DGIM Streaming Analytics', subtitle: 'Exponential histogram for sliding-window bit counting' },
  recommendations: { title: 'Management Recommendations', subtitle: 'Data-driven action items and strategic insights' },
  'data-workspace': { title: 'Data Workspace', subtitle: 'Upload, map, and validate your product data' },
  pipeline: { title: 'Data Pipeline & Evaluation', subtitle: 'Processing stages, validation, and analysis diagnostics' },
};

export function TopBar({ activePage }: { activePage: PageId }) {
  const { dataSource, uploadedDataset, isAnalyzing, analysisMode } = useData();
  const { title, subtitle } = PAGE_TITLES[activePage];
  const isSample = dataSource === 'sample';

  return (
    <header className="bg-white border-b border-slate-200 px-6 py-3.5 sticky top-0 z-10">
      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0">
          <h2 className="text-lg font-semibold text-navy-800 leading-tight">{title}</h2>
          <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          {isAnalyzing && (
            <div className="flex items-center gap-2 text-sm text-teal-600 font-medium animate-fade-in">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Running analysis…</span>
            </div>
          )}

          <div
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs font-medium transition-colors ${
              isSample
                ? 'bg-slate-50 border-slate-200 text-slate-600'
                : 'bg-teal-50 border-teal-200 text-teal-700'
            }`}
          >
            {isSample ? (
              <>
                <Database className="w-3.5 h-3.5 text-slate-400" />
                <span>Sample Dataset</span>
              </>
            ) : (
              <>
                <Upload className="w-3.5 h-3.5 text-teal-500" />
                <span className="max-w-[140px] truncate">{uploadedDataset?.fileName ?? 'My Dataset'}</span>
              </>
            )}
          </div>

          <div
            className={`hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium ${
              analysisMode === 'backend'
                ? 'bg-navy-50 text-navy-600 border border-navy-100'
                : 'bg-slate-50 text-slate-500 border border-slate-200'
            }`}
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>{analysisMode === 'backend' ? 'Backend' : 'Local'} Engine</span>
          </div>
        </div>
      </div>
    </header>
  );
}
