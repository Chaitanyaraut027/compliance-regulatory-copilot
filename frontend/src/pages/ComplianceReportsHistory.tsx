import React, { useEffect, useState } from 'react';
import { complianceApi } from '../api';
import { AuditItem, ComplianceReport } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { formatDate } from '../utils/status';
import {
  FileText,
  Loader2,
  AlertCircle,
  ArrowUpRight,
  Upload,
  Calendar,
  Layers,
} from 'lucide-react';

interface ComplianceReportsHistoryProps {
  onOpenReport: (report: ComplianceReport) => void;
  onNavigateToUpload: () => void;
}

export const ComplianceReportsHistory: React.FC<ComplianceReportsHistoryProps> = ({
  onOpenReport,
  onNavigateToUpload,
}) => {
  const [audits, setAudits] = useState<AuditItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [fetchingId, setFetchingId] = useState<string | number | null>(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await complianceApi.getAuditHistory(50, 0);
      setAudits(res.data || []);
      setTotal(res.pagination?.total ?? (res.data?.length || 0));
    } catch (err: any) {
      setError(
        err.response?.data?.error ||
          'Unable to load compliance history. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSelectReport = async (id: string | number) => {
    setFetchingId(id);
    try {
      const res = await complianceApi.getAuditDetail(id);
      if (res.data) {
        onOpenReport(res.data);
      }
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to load report.');
    } finally {
      setFetchingId(null);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900 dark:text-white">
            Compliance Reports History
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
            View past food compliance evaluations performed on your account.
          </p>
        </div>

        <button
          onClick={onNavigateToUpload}
          className="inline-flex items-center gap-2 px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs rounded-xl shadow-xs transition-colors cursor-pointer self-start md:self-auto"
        >
          <Upload className="w-3.5 h-3.5" />
          <span>New Assessment</span>
        </button>
      </div>

      {loading ? (
        <div className="p-16 flex flex-col items-center justify-center bg-white dark:bg-[#111827] rounded-2xl border border-slate-200 dark:border-slate-800">
          <Loader2 className="w-8 h-8 animate-spin text-sky-600 dark:text-sky-400 mb-3" />
          <p className="text-sm text-slate-500">Loading audit history...</p>
        </div>
      ) : error ? (
        <div className="p-5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-rose-600" />
          <div>{error}</div>
        </div>
      ) : audits.length === 0 ? (
        <div className="p-12 text-center bg-white dark:bg-[#111827] rounded-2xl border border-slate-200 dark:border-slate-800 space-y-4">
          <FileText className="w-12 h-12 text-slate-400 mx-auto" />
          <h2 className="text-lg font-bold text-slate-800 dark:text-slate-200">
            No compliance checks yet
          </h2>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            Upload a product document to create your first automated compliance report.
          </p>
          <button
            onClick={onNavigateToUpload}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-sky-600 hover:bg-sky-500 text-white font-semibold text-sm rounded-lg shadow-xs transition-colors cursor-pointer"
          >
            <Upload className="w-4 h-4" />
            <span>Upload Document Now</span>
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 px-1">
            Total reports found: <strong className="text-slate-800 dark:text-slate-200">{total}</strong>
          </div>

          <div className="bg-white dark:bg-[#111827] rounded-2xl border border-slate-200 dark:border-slate-800 divide-y divide-slate-100 dark:divide-slate-800/80 shadow-xs overflow-hidden">
            {audits.map((a) => {
              const docTitle = a.product_name || a.question || 'Food Product Assessment';
              const isFetchingThis = fetchingId === a.id;

              return (
                <div
                  key={a.id}
                  className="p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-slate-50/50 dark:hover:bg-slate-900/30 transition-colors"
                >
                  <div className="space-y-2 flex-1 pr-4">
                    <div className="flex flex-wrap items-center gap-3">
                      <h2 className="font-bold text-slate-900 dark:text-white text-base">
                        {docTitle}
                      </h2>
                      <StatusBadge status={a.overall_status} size="sm" />
                    </div>

                    <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
                      <span className="flex items-center gap-1.5">
                        <Layers className="w-3.5 h-3.5 text-slate-400" />
                        <span>Area: <strong className="text-slate-700 dark:text-slate-300">{a.compliance_area}</strong></span>
                      </span>
                      <span className="flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        <span>Assessed: <strong className="text-slate-700 dark:text-slate-300">{formatDate(a.created_at)}</strong></span>
                      </span>
                    </div>

                    {a.summary && (
                      <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-3 leading-relaxed">
                        {a.summary}
                      </p>
                    )}
                  </div>

                  <div className="shrink-0">
                    <button
                      onClick={() => handleSelectReport(a.id)}
                      disabled={isFetchingThis}
                      className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg bg-sky-50 hover:bg-sky-100 dark:bg-sky-950/60 dark:hover:bg-sky-900/80 text-sky-700 dark:text-sky-300 transition-colors cursor-pointer disabled:opacity-50"
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
        </div>
      )}
    </div>
  );
};
