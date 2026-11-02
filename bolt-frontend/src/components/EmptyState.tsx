import type { ReactNode } from 'react';
import { Info } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  message: string;
  requiredFields?: string[];
  icon?: ReactNode;
}

export function EmptyState({ title, message, requiredFields, icon }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-12 px-6 bg-slate-50/50 rounded-xl border border-dashed border-slate-300">
      <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mb-3">
        {icon ?? <Info className="w-6 h-6 text-slate-400" />}
      </div>
      <h3 className="text-base font-semibold text-slate-700 mb-1">{title}</h3>
      <p className="text-sm text-slate-500 max-w-md">{message}</p>
      {requiredFields && requiredFields.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2 justify-center">
          {requiredFields.map((f) => (
            <span key={f} className="px-2.5 py-1 text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200 rounded-md">
              {f}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
