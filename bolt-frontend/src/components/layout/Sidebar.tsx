import { useState } from 'react';
import {
  LayoutDashboard, BarChart3, AlertTriangle, Lightbulb, Database,
  Rocket, Filter, Activity, GitBranch, Menu, X,
} from 'lucide-react';

export type PageId =
  | 'dashboard'
  | 'features'
  | 'task-risk'
  | 'bloom-filter'
  | 'dgim'
  | 'recommendations'
  | 'data-workspace'
  | 'pipeline';

interface SidebarProps {
  activePage: PageId;
  onNavigate: (page: PageId) => void;
}

const NAV_SECTIONS: { heading: string; items: { id: PageId; label: string; icon: typeof LayoutDashboard }[] }[] = [
  {
    heading: 'Analytics',
    items: [
      { id: 'dashboard', label: 'Executive Overview', icon: LayoutDashboard },
      { id: 'features', label: 'Feature Prioritization', icon: BarChart3 },
      { id: 'task-risk', label: 'Project Delivery Risks', icon: AlertTriangle },
    ],
  },
  {
    heading: 'Algorithms',
    items: [
      { id: 'bloom-filter', label: 'Bloom Filter Laboratory', icon: Filter },
      { id: 'dgim', label: 'DGIM Streaming Analytics', icon: Activity },
    ],
  },
  {
    heading: 'Management',
    items: [
      { id: 'recommendations', label: 'Recommendations', icon: Lightbulb },
      { id: 'pipeline', label: 'Data Pipeline & Evaluation', icon: GitBranch },
    ],
  },
  {
    heading: 'Data',
    items: [
      { id: 'data-workspace', label: 'Data Workspace', icon: Database },
    ],
  },
];

export function Sidebar({ activePage, onNavigate }: SidebarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  const sidebar = (
    <aside className="w-60 bg-navy-900 text-navy-50 flex flex-col h-full shrink-0">
      {/* Brand */}
      <div className="px-4 py-4 border-b border-navy-700/60 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-teal-500 flex items-center justify-center shrink-0">
            <Rocket className="w-4.5 h-4.5 text-navy-900" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-white leading-tight">ProductPilot</h1>
            <p className="text-[10px] text-navy-300 leading-tight">Analytics Platform</p>
          </div>
        </div>
        <button onClick={() => setMobileOpen(false)} className="lg:hidden text-navy-300 hover:text-white">
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto scrollbar-thin py-2 px-2">
        {NAV_SECTIONS.map((section) => (
          <div key={section.heading} className="mb-1">
            <p className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-navy-500">{section.heading}</p>
            {section.items.map((item) => {
              const Icon = item.icon;
              const active = activePage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => { onNavigate(item.id); setMobileOpen(false); }}
                  className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg mb-0.5 transition-all duration-150 group focus:outline-none focus:ring-2 focus:ring-teal-400/40 ${
                    active
                      ? 'bg-teal-500/15 text-white'
                      : 'text-navy-200 hover:bg-navy-700/40 hover:text-white'
                  }`}
                  aria-current={active ? 'page' : undefined}
                >
                  <Icon
                    className={`w-4 h-4 shrink-0 transition-colors ${active ? 'text-teal-400' : 'text-navy-400 group-hover:text-teal-300'}`}
                  />
                  <span className="text-sm font-medium leading-tight">{item.label}</span>
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-3 py-3 border-t border-navy-700/60">
        <div className="flex items-center gap-2 text-[10px] text-navy-400">
          <div className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
          <span>Local analysis engine</span>
        </div>
      </div>
    </aside>
  );

  return (
    <>
      {/* Mobile toggle */}
      <button
        onClick={() => setMobileOpen(true)}
        className="lg:hidden fixed top-3 left-3 z-50 w-9 h-9 rounded-lg bg-navy-800 text-white flex items-center justify-center shadow-md"
        aria-label="Open navigation"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Desktop sidebar */}
      <div className="hidden lg:block sticky top-0 h-screen shrink-0">{sidebar}</div>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-40 flex">
          <div className="absolute inset-0 bg-black/40" onClick={() => setMobileOpen(false)} />
          <div className="relative h-full">{sidebar}</div>
        </div>
      )}
    </>
  );
}
