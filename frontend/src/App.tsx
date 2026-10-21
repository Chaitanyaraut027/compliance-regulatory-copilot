import React, { useState } from 'react';
import { useAuth } from './context/AuthContext';
import { NavView, ComplianceReport } from './types';
import { Sidebar } from './components/Sidebar';
import { AuthPage } from './pages/AuthPage';
import { Dashboard } from './pages/Dashboard';
import { UploadDocument } from './pages/UploadDocument';
import { ComplianceReportsHistory } from './pages/ComplianceReportsHistory';
import { ComplianceReportView } from './pages/ComplianceReportView';
import { SearchRegulations } from './pages/SearchRegulations';
import { Menu } from 'lucide-react';

export const AppContent: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [currentView, setCurrentView] = useState<NavView>('Dashboard');
  const [currentReport, setCurrentReport] = useState<ComplianceReport | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // If not logged in, show Auth Page (Login / Register)
  if (!isAuthenticated) {
    return <AuthPage />;
  }

  const handleNavigate = (view: NavView) => {
    setCurrentView(view);
    setCurrentReport(null);
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#090d16] text-slate-900 dark:text-slate-100 flex">
      {/* Sidebar */}
      <Sidebar
        currentView={currentView}
        onNavigate={handleNavigate}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main Content Area */}
      <div className="flex-1 lg:pl-64 flex flex-col min-h-screen min-w-0">
        {/* Mobile Top Header */}
        <header className="lg:hidden sticky top-0 z-30 flex items-center justify-between px-4 py-3 bg-white dark:bg-[#111827] border-b border-slate-200 dark:border-slate-800">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 -ml-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg cursor-pointer"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div>
            <span className="font-bold text-sm text-slate-900 dark:text-white">
              Food Compliance Portal
            </span>
          </div>
          <div className="w-7" />
        </header>

        {/* Page Content Body */}
        <main className="flex-1 p-4 md:p-8 max-w-7xl mx-auto w-full">
          {currentReport ? (
            <ComplianceReportView
              report={currentReport}
              onCheckAnother={() => {
                setCurrentReport(null);
                setCurrentView('Upload Document');
              }}
              onBackToDashboard={() => {
                setCurrentReport(null);
                setCurrentView('Dashboard');
              }}
            />
          ) : (
            <>
              {currentView === 'Dashboard' && (
                <Dashboard
                  onNavigateToUpload={() => setCurrentView('Upload Document')}
                  onOpenReport={(report) => setCurrentReport(report)}
                />
              )}

              {currentView === 'Upload Document' && (
                <UploadDocument
                  onReportGenerated={(report) => setCurrentReport(report)}
                />
              )}

              {currentView === 'Compliance Reports' && (
                <ComplianceReportsHistory
                  onOpenReport={(report) => setCurrentReport(report)}
                  onNavigateToUpload={() => setCurrentView('Upload Document')}
                />
              )}

              {currentView === 'Search Regulations' && <SearchRegulations />}
            </>
          )}
        </main>
      </div>
    </div>
  );
};
