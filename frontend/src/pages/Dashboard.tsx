import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { complianceApi } from '../api';
import { AuditItem, ComplianceReport } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { formatDate } from '../utils/status';
import {
  Upload,
  ArrowUpRight,
  ClipboardList,
  Loader2,
  AlertCircle,
  FileCheck2,
} from 'lucide-react';

interface DashboardProps {
  onNavigateToUpload: () => void;
  onOpenReport: (report: ComplianceReport) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  onNavigateToUpload,
  onOpenReport,
}) => {
  const { user } = useAuth();
  const [audits, setAudits] = useState<AuditItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [loadingReportId, setLoadingReportId] = useState<string | number | null>(null);

  useEffect(() => {
    fetchRecentAudits();
  }, []);

  const fetchRecentAudits = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await complianceApi.getAuditHistory(5, 0);
      setAudits(resp.data || []);
      setTotal(resp.pagination?.total ?? (resp.data?.length || 0));
    } catch (err: any) {
      console.error(err);
      setError(
        err.response?.data?.error ||
          'Unable to load recent compliance checks. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleViewReport = async (id: string | number) => {
    setLoadingReportId(id);
    try {
      const resp = await complianceApi.getAuditDetail(id);
      if (resp.data) {
        onOpenReport(resp.data);
      }
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to fetch full report details.');
    } finally {
      setLoadingReportId(null);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Welcome Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 dark:text-white">
          Welcome, {user?.name || 'User'}
        </h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm md:text-base mt-1.5 max-w-3xl leading-relaxed">
          Verify food product specifications, ingredient lists, and package labels
          against official food safety regulations.
        </p>
      </div>

      {/* Primary CTA Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-sky-500/15 via-sky-400/10 to-transparent border border-sky-500/30 dark:border-sky-500/20 p-6 md:p-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="max-w-2xl">
            <h2 className="text-lg md:text-xl font-bold text-sky-950 dark:text-sky-300">
              Evaluate a food product
            </h2>
            <p className="text-slate-700 dark:text-slate-300 text-sm mt-1.5 leading-relaxed">
              Upload a product specification sheet, label draft, or ingredient declaration (PDF or TXT, max 5 MB).
              The system will evaluate it against official food safety standards and return a full compliance report.
            </p>
          </div>
          <button
            onClick={onNavigateToUpload}
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-sky-600 hover:bg-sky-500 text-white font-semibold rounded-xl shadow-sm transition-all hover:shadow cursor-pointer shrink-0 text-sm"
          >
            <Upload className="w-4 h-4" />
            <span>Upload Document</span>
          </button>
        </div>
      </div>

      {/* Recent Compliance Checks */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ClipboardList className="w-5 h-5 text-sky-600 dark:text-sky-400" />
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">
              Recent Compliance Checks
            </h2>
          </div>
          {total > 0 && (
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Showing {audits.length} of {total} total
            </span>
          )}
        </div>

        {loading ? (
          <div className="p-12 flex flex-col items-center justify-center bg-white dark:bg-[#111827] rounded-xl border border-slate-200 dark:border-slate-800">
            <Loader2 className="w-8 h-8 animate-spin text-sky-600 dark:text-sky-400 mb-3" />
            <p className="text-sm text-slate-500">Loading recent assessments...</p>
          </div>
        ) : error ? (
          <div className="p-5 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/60 text-amber-800 dark:text-amber-200 text-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-amber-600" />
            <div>{error}</div>
          </div>
        ) : audits.length === 0 ? (
          <div className="p-10 text-center bg-white dark:bg-[#111827] rounded-xl border border-slate-200 dark:border-slate-800">
            <FileCheck2 className="w-12 h-12 text-slate-400 mx-auto mb-3" />
            <h3 className="font-semibold text-slate-800 dark:text-slate-200">
              No compliance checks yet
            </h3>
            <p className="text-sm text-slate-500 mt-1 max-w-md mx-auto">
              Upload your first food product document above to generate an automated regulatory compliance report.
            </p>
          </div>
        ) : (
          <div className="bg-white dark:bg-[#111827] rounded-xl border border-slate-200 dark:border-slate-800 divide-y divide-slate-100 dark:divide-slate-800/80 shadow-xs">
            {audits.map((a) => {
              const docTitle = a.product_name || a.question || 'Food Product Specification';
              const isFetchingThis = loadingReportId === a.id;

              return (
                <div
                  key={a.id}
                  className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-slate-50/50 dark:hover:bg-slate-900/30 transition-colors"
                >
                  <div className="space-y-1.5 flex-1 pr-4">
                    <div className="flex flex-wrap items-center gap-2.5">
                      <h3 className="font-semibold text-slate-900 dark:text-white text-base">
                        {docTitle}
                      </h3>
                      <StatusBadge status={a.overall_status} size="sm" />
                    </div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">
                      Area: <strong className="text-slate-700 dark:text-slate-300">{a.compliance_area}</strong> • Assessed: {formatDate(a.created_at)}
                    </div>
                    {a.summary && (
                      <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2 leading-relaxed">
                        {a.summary}
                      </p>
                    )}
                  </div>

                  <div className="shrink-0">
                    <button
                      onClick={() => handleViewReport(a.id)}
                      disabled={isFetchingThis}
                      className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 transition-colors cursor-pointer disabled:opacity-50"
                    >
                      {isFetchingThis ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      )}
                      <span>View Report</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
