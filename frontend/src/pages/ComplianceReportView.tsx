import React, { useState, useRef, useEffect } from 'react';
import { ComplianceReport } from '../types';
import { mapStatus, formatDate } from '../utils/status';
import { StatusBadge } from '../components/StatusBadge';
import {
  ChevronDown,
  ChevronUp,
  FileCheck2,
  AlertTriangle,
  Info,
  CheckCircle2,
  BookOpen,
  ArrowLeft,
  Upload,
  Download,
  Printer,
  FileText,
} from 'lucide-react';

interface ComplianceReportViewProps {
  report: ComplianceReport;
  onCheckAnother: () => void;
  onBackToDashboard: () => void;
}

export const ComplianceReportView: React.FC<ComplianceReportViewProps> = ({
  report,
  onCheckAnother,
  onBackToDashboard,
}) => {
  const statusInfo = mapStatus(report.overall_status);
  const docName = report.product_name || report.question || 'Food Product Specification';
  const displayDate = formatDate(report.created_at || new Date().toISOString());

  const findings = report.findings || [];
  const satisfied = findings.filter((f) => mapStatus(f.status).category === 'satisfied');
  const attention = findings.filter((f) => mapStatus(f.status).category === 'attention');
  const insufficient = findings.filter((f) => mapStatus(f.status).category === 'insufficient');

  const [activeTab, setActiveTab] = useState<'attention' | 'satisfied' | 'insufficient' | 'all'>(
    attention.length > 0 ? 'attention' : 'all'
  );

  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Expanded cards state
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {};
    findings.forEach((f, idx) => {
      // Default expand non-satisfied findings
      const cat = mapStatus(f.status).category;
      initial[`card_${idx}`] = cat !== 'satisfied';
    });
    return initial;
  });

  const toggleCard = (key: string) => {
    setExpandedCards((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const getFilteredFindings = () => {
    switch (activeTab) {
      case 'attention':
        return attention;
      case 'satisfied':
        return satisfied;
      case 'insufficient':
        return insufficient;
      default:
        return findings;
    }
  };

  const currentFindingsList = getFilteredFindings();

  // ── Download Helpers ──────────────────────────────────────────

  // 1. Download PDF / Print
  const handlePrintPDF = () => {
    setDropdownOpen(false);
    // Expand all cards & show all findings so the generated PDF is complete
    const allExpanded: Record<string, boolean> = {};
    findings.forEach((_, idx) => {
      allExpanded[`card_${idx}`] = true;
    });
    setExpandedCards(allExpanded);
    setActiveTab('all');

    setTimeout(() => {
      window.print();
    }, 200);
  };

  // 2. Download Formatted Text Report (.txt)
  const handleDownloadText = () => {
    setDropdownOpen(false);
    const lines = [
      `========================================================================`,
      `FOOD COMPLIANCE ASSESSMENT REPORT`,
      `========================================================================`,
      `Product / Document:  ${docName}`,
      `Compliance Area:     ${report.compliance_area || 'Food Safety Standards'}`,
      `Date of Analysis:    ${displayDate}`,
      `Overall Status:      ${statusInfo.label.toUpperCase()} (${report.overall_status})`,
      `------------------------------------------------------------------------`,
      `EXECUTIVE SUMMARY:`,
      report.summary || 'No summary available.',
      ``,
      `------------------------------------------------------------------------`,
      `EVALUATION METRICS:`,
      `- Total Requirements Evaluated: ${findings.length}`,
      `- Satisfied Requirements:       ${satisfied.length}`,
      `- Needs Attention:             ${attention.length}`,
      `- Missing Information:         ${insufficient.length}`,
      ``,
      `------------------------------------------------------------------------`,
      `DETAILED REQUIREMENTS BREAKDOWN:`,
      ``,
      ...findings.map((f, i) => {
        const fInfo = mapStatus(f.status);
        const evFound = (f.evidence_found || []).map((e) => `   [+] Evidence: ${e}`).join('\n');
        const evMissing = (f.evidence_missing || []).map((e) => `   [-] Missing:  ${e}`).join('\n');
        const actions = (f.recommended_actions || []).map((a) => `   [*] Action:   ${a}`).join('\n');
        const sources = (f.regulatory_sources || report.retrieved_sources || [])
          .slice(0, 3)
          .map((s) => `   [Ref] ${s.document_name || s.doc_title || 'Regulation'} (Page ${s.page_start || 'N/A'})`)
          .join('\n');

        return [
          `#${i + 1}. [${fInfo.label.toUpperCase()}] ${f.requirement}`,
          `   Status:      ${f.status}`,
          `   Explanation: ${f.explanation}`,
          evFound,
          evMissing,
          actions,
          sources,
          ``,
        ]
          .filter(Boolean)
          .join('\n');
      }),
      `------------------------------------------------------------------------`,
      `NOTICE:`,
      report.disclaimer ||
        'This compliance assessment is generated using official regulatory reference documents for informational purposes. It does not constitute formal legal certification.',
      `========================================================================`,
    ];

    const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const safeTitle = (docName || 'compliance_report')
      .replace(/[^a-zA-Z0-9_-]/g, '_')
      .toLowerCase();
    const link = document.createElement('a');
    link.href = url;
    link.download = `${safeTitle}_compliance_report.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      {/* Top Navigation & Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 no-print">
        <button
          onClick={onBackToDashboard}
          className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </button>

        <div className="flex items-center gap-2.5">
          {/* Download Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen((prev) => !prev)}
              className="inline-flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition-colors shadow-xs cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download Report</span>
              <ChevronDown className="w-3.5 h-3.5 opacity-80" />
            </button>

            {dropdownOpen && (
              <div className="absolute right-0 mt-1.5 w-52 rounded-xl bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 shadow-xl z-50 py-1 text-xs divide-y divide-slate-100 dark:divide-slate-800">
                <div className="py-1">
                  <button
                    onClick={handlePrintPDF}
                    className="w-full px-3.5 py-2 flex items-center gap-2.5 hover:bg-slate-50 dark:hover:bg-slate-800/60 text-slate-700 dark:text-slate-200 text-left cursor-pointer"
                  >
                    <Printer className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                    <div>
                      <div className="font-semibold">Print / Save as PDF</div>
                      <div className="text-[10px] text-slate-400">Printable document</div>
                    </div>
                  </button>

                  <button
                    onClick={handleDownloadText}
                    className="w-full px-3.5 py-2 flex items-center gap-2.5 hover:bg-slate-50 dark:hover:bg-slate-800/60 text-slate-700 dark:text-slate-200 text-left cursor-pointer"
                  >
                    <FileText className="w-4 h-4 text-sky-600 dark:text-sky-400" />
                    <div>
                      <div className="font-semibold">Summary Text (.txt)</div>
                      <div className="text-[10px] text-slate-400">Plain text file</div>
                    </div>
                  </button>
                </div>
              </div>
            )}
          </div>

          <button
            onClick={onCheckAnother}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-sky-600 hover:bg-sky-500 text-white transition-colors shadow-xs cursor-pointer"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Check Another Document</span>
          </button>
        </div>
      </div>

      {/* Main Header Card */}
      <div
        className="bg-white dark:bg-[#111827] rounded-2xl border border-slate-200 dark:border-slate-800 p-6 md:p-8 shadow-sm break-inside-avoid"
        style={{ borderTop: `4px solid ${statusInfo.badgeColor}` }}
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-100 dark:border-slate-800/80">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              Product Compliance Analysis
            </span>
            <h1 className="text-2xl md:text-3xl font-bold text-slate-900 dark:text-white mt-1">
              {docName}
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Date:{' '}
              <span className="font-semibold text-slate-700 dark:text-slate-300">
                {displayDate}
              </span>
              {report.compliance_area && (
                <>
                  {' '}
                  • Category:{' '}
                  <span className="font-semibold text-slate-700 dark:text-slate-300">
                    {report.compliance_area}
                  </span>
                </>
              )}
            </p>
          </div>

          <div>
            <StatusBadge status={report.overall_status} size="lg" />
          </div>
        </div>

        {/* Executive Summary */}
        <div className="mt-6 p-4 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-800">
          <h2 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2">
            <FileCheck2 className="w-4 h-4 text-sky-600 dark:text-sky-400" />
            <span>Executive Summary</span>
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-slate-700 dark:text-slate-300">
            {report.summary || 'No detailed summary available.'}
          </p>
        </div>

        {/* Disclaimer Notice Banner */}
        <div className="mt-4 p-3.5 rounded-xl bg-slate-100 dark:bg-slate-800/60 border-l-4 border-slate-400 dark:border-sky-500 text-xs text-slate-600 dark:text-slate-300">
          <strong className="text-slate-800 dark:text-slate-200">Notice: </strong>
          {report.disclaimer ||
            'This compliance assessment is generated for regulatory verification and pre-audit guidance purposes. It does not constitute formal legal certification.'}
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 break-inside-avoid">
        <div className="bg-white dark:bg-[#111827] p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
          <div className="text-xs font-semibold text-slate-500 dark:text-slate-400">
            Total Evaluated
          </div>
          <div className="text-3xl font-bold text-slate-900 dark:text-white mt-1">
            {findings.length}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Requirements</div>
        </div>

        <div className="bg-white dark:bg-[#111827] p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
          <div className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Satisfied</span>
          </div>
          <div className="text-3xl font-bold text-emerald-700 dark:text-emerald-400 mt-1">
            {satisfied.length}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Compliant</div>
        </div>

        <div className="bg-white dark:bg-[#111827] p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
          <div className="text-xs font-semibold text-amber-600 dark:text-amber-400 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Needs Attention</span>
          </div>
          <div className="text-3xl font-bold text-amber-700 dark:text-amber-400 mt-1">
            {attention.length}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Action required</div>
        </div>

        <div className="bg-white dark:bg-[#111827] p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
          <div className="text-xs font-semibold text-blue-600 dark:text-blue-400 flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5" />
            <span>Missing Information</span>
          </div>
          <div className="text-3xl font-bold text-blue-700 dark:text-blue-400 mt-1">
            {insufficient.length}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Requires evidence</div>
        </div>
      </div>

      {/* Breakdown Section */}
      <div className="bg-white dark:bg-[#111827] rounded-2xl border border-slate-200 dark:border-slate-800 p-6 md:p-8 shadow-sm">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">
          Requirements Breakdown
        </h2>

        {/* Filter Tabs (Hidden in print so all findings appear) */}
        <div className="flex flex-wrap gap-2 pb-4 border-b border-slate-200 dark:border-slate-800 no-print">
          <button
            onClick={() => setActiveTab('attention')}
            className={`px-3.5 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'attention'
                ? 'bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300 ring-1 ring-amber-300 dark:ring-amber-800'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            Needs Attention ({attention.length})
          </button>
          <button
            onClick={() => setActiveTab('satisfied')}
            className={`px-3.5 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'satisfied'
                ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 ring-1 ring-emerald-300 dark:ring-emerald-800'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            Satisfied ({satisfied.length})
          </button>
          <button
            onClick={() => setActiveTab('insufficient')}
            className={`px-3.5 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'insufficient'
                ? 'bg-blue-100 dark:bg-blue-950 text-blue-800 dark:text-blue-300 ring-1 ring-blue-300 dark:ring-blue-800'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            Missing Information ({insufficient.length})
          </button>
          <button
            onClick={() => setActiveTab('all')}
            className={`px-3.5 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'all'
                ? 'bg-slate-200 dark:bg-slate-700 text-slate-900 dark:text-white'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            All Requirements ({findings.length})
          </button>
        </div>

        {/* Findings List */}
        <div className="mt-5 space-y-3.5">
          {currentFindingsList.length === 0 ? (
            <div className="p-8 text-center text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-900/40 rounded-xl border border-dashed border-slate-200 dark:border-slate-800">
              No requirements in this category.
            </div>
          ) : (
            currentFindingsList.map((f, i) => {
              const cardKey = `card_${findings.indexOf(f)}`;
              const isExpanded = !!expandedCards[cardKey];

              return (
                <div
                  key={cardKey}
                  className="rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden bg-slate-50/50 dark:bg-slate-900/40 transition-colors break-inside-avoid print:bg-white print:border-slate-300 print:mb-6"
                >
                  <div
                    role="button"
                    tabIndex={0}
                    onClick={() => toggleCard(cardKey)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        toggleCard(cardKey);
                      }
                    }}
                    className="w-full px-5 py-4 flex items-center justify-between text-left hover:bg-slate-100/60 dark:hover:bg-slate-800/40 transition-colors cursor-pointer print:bg-slate-50 print:border-b print:border-slate-200"
                  >
                    <div className="flex items-center gap-3 pr-4">
                      <div>
                        <div className="font-semibold text-sm text-slate-900 dark:text-white print:text-base print:font-bold">
                          <span className="text-slate-500 mr-1.5">#{i + 1}</span>
                          {f.requirement || 'Regulatory Requirement'}
                        </div>
                        <div className="mt-1">
                          <StatusBadge status={f.status} size="sm" />
                        </div>
                      </div>
                    </div>
                    <div className="no-print">
                      {isExpanded ? (
                        <ChevronUp className="w-5 h-5 text-slate-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-slate-400" />
                      )}
                    </div>
                  </div>

                  {(isExpanded || true) && (
                    <div
                      className={`px-5 pb-5 pt-2 border-t border-slate-200/60 dark:border-slate-800/60 text-sm space-y-4 ${
                        !isExpanded ? 'hidden print:block' : ''
                      }`}
                    >
                      <div>
                        <strong className="text-xs uppercase tracking-wider text-slate-400">
                          Explanation:
                        </strong>
                        <p className="mt-1 text-slate-700 dark:text-slate-300 leading-relaxed">
                          {f.explanation || 'No detailed explanation provided.'}
                        </p>
                      </div>

                      {/* Evidence Found */}
                      {f.evidence_found && f.evidence_found.length > 0 && (
                        <div>
                          <strong className="text-xs font-semibold text-emerald-700 dark:text-emerald-400">
                            Evidence Found in Document:
                          </strong>
                          <ul className="mt-1.5 space-y-1">
                            {f.evidence_found.map((item, idx) => (
                              <li
                                key={idx}
                                className="flex items-start gap-2 text-slate-700 dark:text-slate-300 text-xs md:text-sm"
                              >
                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                                <span>{item}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Missing Evidence */}
                      {f.evidence_missing && f.evidence_missing.length > 0 && (
                        <div>
                          <strong className="text-xs font-semibold text-amber-700 dark:text-amber-400">
                            Missing Information / Evidence Required:
                          </strong>
                          <ul className="mt-1.5 space-y-1">
                            {f.evidence_missing.map((item, idx) => (
                              <li
                                key={idx}
                                className="flex items-start gap-2 text-slate-700 dark:text-slate-300 text-xs md:text-sm"
                              >
                                <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
                                <span>{item}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Corrective Actions */}
                      {f.recommended_actions && f.recommended_actions.length > 0 && (
                        <div>
                          <strong className="text-xs font-semibold text-sky-700 dark:text-sky-400">
                            Suggested Corrective Actions:
                          </strong>
                          <ul className="mt-1.5 space-y-1">
                            {f.recommended_actions.map((act, idx) => (
                              <li
                                key={idx}
                                className="flex items-start gap-2 text-slate-700 dark:text-slate-300 text-xs md:text-sm"
                              >
                                <Info className="w-3.5 h-3.5 text-sky-600 shrink-0 mt-0.5" />
                                <span>{act}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Supporting Regulatory References */}
                      {((f.regulatory_sources && f.regulatory_sources.length > 0) ||
                        (report.retrieved_sources && report.retrieved_sources.length > 0)) && (
                        <div className="pt-2 border-t border-slate-200/50 dark:border-slate-800/50">
                          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 flex items-center gap-1.5 mb-1.5">
                            <BookOpen className="w-3.5 h-3.5 text-slate-400" />
                            <span>Official Regulatory References:</span>
                          </span>
                          <div className="space-y-1">
                            {(f.regulatory_sources || report.retrieved_sources || [])
                              .slice(0, 3)
                              .map((s, idx) => {
                                const docTitle =
                                  s.document_name ||
                                  s.doc_title ||
                                  s.doc_filename ||
                                  'Regulatory Standard';
                                const pages = s.page_start
                                  ? `Pages ${s.page_start}–${s.page_end}`
                                  : '';
                                const sec = s.section ? ` | Section: ${s.section}` : '';
                                return (
                                  <div
                                    key={idx}
                                    className="text-xs text-slate-600 dark:text-slate-400 bg-white/60 dark:bg-slate-800/50 p-2 rounded border border-slate-200/60 dark:border-slate-700/50"
                                  >
                                    <strong className="text-slate-800 dark:text-slate-200">{docTitle}</strong>{' '}
                                    {pages} {sec}
                                  </div>
                                );
                              })}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Bottom Actions */}
        <div className="mt-8 pt-6 border-t border-slate-200 dark:border-slate-800 flex flex-wrap items-center gap-3 no-print">
          <button
            onClick={handlePrintPDF}
            className="px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs md:text-sm shadow-xs transition-colors cursor-pointer inline-flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            <span>Download Report (PDF)</span>
          </button>
          <button
            onClick={handleDownloadText}
            className="px-4 py-2.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 font-semibold text-xs md:text-sm transition-colors cursor-pointer inline-flex items-center gap-1.5"
          >
            <FileText className="w-4 h-4" />
            <span>Export Text (.txt)</span>
          </button>
          <button
            onClick={onCheckAnother}
            className="px-5 py-2.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs md:text-sm shadow-xs transition-colors cursor-pointer"
          >
            Check Another Document
          </button>
          <button
            onClick={onBackToDashboard}
            className="px-5 py-2.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 font-semibold text-xs md:text-sm transition-colors cursor-pointer"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};
