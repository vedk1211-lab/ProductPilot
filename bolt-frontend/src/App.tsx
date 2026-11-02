import { useState } from 'react';
import { DataProvider } from '@/context/DataContext';
import { Sidebar, type PageId } from '@/components/layout/Sidebar';
import { TopBar } from '@/components/layout/TopBar';
import { DashboardPage } from '@/pages/DashboardPage';
import { FeaturesPage } from '@/pages/FeaturesPage';
import { TaskRiskPage } from '@/pages/TaskRiskPage';
import { BloomFilterPage } from '@/pages/BloomFilterPage';
import { DgimPage } from '@/pages/DgimPage';
import { RecommendationsPage } from '@/pages/RecommendationsPage';
import { DataWorkspacePage } from '@/pages/DataWorkspacePage';
import { PipelinePage } from '@/pages/PipelinePage';

function App() {
  const [activePage, setActivePage] = useState<PageId>('dashboard');

  return (
    <DataProvider>
      <div className="flex min-h-screen bg-slate-50">
        <Sidebar activePage={activePage} onNavigate={setActivePage} />
        <div className="flex-1 flex flex-col min-w-0">
          <TopBar activePage={activePage} />
          <main className="flex-1 overflow-y-auto scrollbar-thin">
            {activePage === 'dashboard' && <DashboardPage />}
            {activePage === 'features' && <FeaturesPage />}
            {activePage === 'task-risk' && <TaskRiskPage />}
            {activePage === 'bloom-filter' && <BloomFilterPage />}
            {activePage === 'dgim' && <DgimPage />}
            {activePage === 'recommendations' && <RecommendationsPage />}
            {activePage === 'data-workspace' && <DataWorkspacePage />}
            {activePage === 'pipeline' && <PipelinePage />}
          </main>
        </div>
      </div>
    </DataProvider>
  );
}

export default App;
