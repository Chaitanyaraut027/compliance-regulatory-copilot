import React, { useState, useRef } from 'react';
import { complianceApi } from '../api';
import { ComplianceReport } from '../types';
import {
  Upload,
  FileText,
  AlertCircle,
  CheckCircle2,
  Loader2,
  X,
  FileCheck,
  FileCheck2,
} from 'lucide-react';

interface UploadDocumentProps {
  onReportGenerated: (report: ComplianceReport) => void;
}

const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB

const COMPLIANCE_AREAS = [
  'General Labelling & Display',
  'Food Additives',
  'Contaminants & Residues',
  'Licensing & Registration',
  'Hygiene & Sanitary Practices',
];

export const UploadDocument: React.FC<UploadDocumentProps> = ({ onReportGenerated }) => {
  const [file, setFile] = useState<File | null>(null);
  const [productName, setProductName] = useState('');
  const [complianceArea, setComplianceArea] = useState(COMPLIANCE_AREAS[0]);
  const [facilityInfo, setFacilityInfo] = useState('');

  // Processing state
  const [isProcessing, setIsProcessing] = useState(false);
  const [progressPercent, setProgressPercent] = useState(0);
  const [progressStatus, setProgressStatus] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (selectedFile: File | null) => {
    setErrorMessage(null);
    if (!selectedFile) return;

    if (selectedFile.size > MAX_FILE_SIZE_BYTES) {
      setErrorMessage(
        `File size (${(selectedFile.size / (1024 * 1024)).toFixed(
          2
        )} MB) exceeds the maximum allowed limit of 5 MB.`
      );
      setFile(null);
      return;
    }

    const ext = selectedFile.name.split('.').pop()?.toLowerCase();
    if (ext !== 'pdf' && ext !== 'txt') {
      setErrorMessage('Please select a valid PDF or TXT document.');
      return;
    }

    setFile(selectedFile);
    // Auto populate product name from filename if not yet filled
    if (!productName) {
      const base = selectedFile.name.replace(/\.[^/.]+$/, '').replace(/_/g, ' ');
      setProductName(base.charAt(0).toUpperCase() + base.slice(1));
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setErrorMessage('Please select a food product document (PDF or TXT) before checking compliance.');
      return;
    }

    setIsProcessing(true);
    setErrorMessage(null);
    setProgressPercent(15);
    setProgressStatus('Uploading document...');

    try {
      // Step 1: Upload to Node.js backend to extract text
      const uploadResp = await complianceApi.uploadDocument(file);
      const extractedText = (uploadResp.extracted_text || '').trim();

      if (extractedText.length < 15) {
        throw new Error(
          'The uploaded document contains little to no readable text. Please upload a document with readable text or specifications.'
        );
      }

      setProgressPercent(45);
      setProgressStatus('Reading document and finding applicable food standards...');

      await new Promise((r) => setTimeout(r, 600));

      setProgressPercent(70);
      setProgressStatus('Evaluating product evidence against safety requirements...');

      // Step 2: Analyse via Node.js -> FastAPI RAG
      const questionText = `Assess regulatory compliance for product document '${
        productName.trim() || file.name
      }' against mandatory standards, labelling rules, safety thresholds, and permitted additives.`;

      const checkPayload = {
        question: questionText,
        company_evidence: extractedText,
        compliance_area: complianceArea,
        facility_description: facilityInfo.trim() || null,
        product_name: productName.trim() || file.name,
        top_k: 5,
      };

      const checkResp = await complianceApi.checkCompliance(checkPayload);

      setProgressPercent(100);
      setProgressStatus('Evaluation complete! Opening report...');

      await new Promise((r) => setTimeout(r, 400));

      if (checkResp.data) {
        onReportGenerated(checkResp.data);
      } else {
        throw new Error('No assessment payload returned.');
      }
    } catch (err: any) {
      console.error(err);
      const msg =
        err.response?.data?.error ||
        err.message ||
        'Compliance check could not be completed. Please try again.';
      setErrorMessage(msg);
      setIsProcessing(false);
      setProgressPercent(0);
      setProgressStatus('');
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 dark:text-white">
          Upload Food Product Document
        </h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm mt-1.5 leading-relaxed">
          Upload your food product specification, ingredient declaration, or label draft.
          The system will check the contents against official food safety regulations and generate a compliance report.
        </p>
      </div>

      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-rose-600" />
          <div className="flex-1">{errorMessage}</div>
          <button
            onClick={() => setErrorMessage(null)}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {isProcessing && (
        <div className="bg-white dark:bg-[#111827] rounded-2xl border border-sky-200 dark:border-sky-900/50 p-6 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-sky-600" />
              <span>{progressStatus}</span>
            </span>
            <span className="font-mono text-xs text-sky-600 dark:text-sky-400 font-bold">
              {progressPercent}%
            </span>
          </div>
          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2.5 overflow-hidden">
            <div
              className="bg-sky-600 h-2.5 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <p className="text-xs text-slate-400 dark:text-slate-500 text-center">
            Verification may take 10 to 20 seconds...
          </p>
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="bg-white dark:bg-[#111827] rounded-2xl border border-slate-200 dark:border-slate-800 p-6 md:p-8 shadow-sm space-y-6"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Column 1: Document Upload */}
          <div className="space-y-4">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              1. Select Document
            </h2>

            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
                file
                  ? 'border-emerald-400 bg-emerald-50/40 dark:bg-emerald-950/20'
                  : 'border-slate-300 dark:border-slate-700 hover:border-sky-500 hover:bg-slate-50 dark:hover:bg-slate-900/40'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleFileChange(e.target.files[0]);
                  }
                }}
              />

              {file ? (
                <div className="flex flex-col items-center">
                  <div className="w-12 h-12 rounded-xl bg-emerald-100 dark:bg-emerald-900/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mb-2">
                    <FileCheck className="w-6 h-6" />
                  </div>
                  <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 truncate max-w-xs">
                    {file.name}
                  </p>
                  <p className="text-xs text-emerald-600 dark:text-emerald-400 mt-1">
                    {(file.size / 1024).toFixed(1)} KB • Ready for analysis
                  </p>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setFile(null);
                    }}
                    className="mt-3 text-xs text-rose-500 hover:underline inline-flex items-center gap-1"
                  >
                    <X className="w-3.5 h-3.5" /> Remove file
                  </button>
                </div>
              ) : (
                <div className="flex flex-col items-center">
                  <div className="w-12 h-12 rounded-xl bg-sky-50 dark:bg-sky-950/60 text-sky-600 dark:text-sky-400 flex items-center justify-center mb-2">
                    <Upload className="w-6 h-6" />
                  </div>
                  <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                    Click to select or drag & drop file
                  </p>
                  <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                    PDF or TXT documents (Max 5 MB)
                  </p>
                  <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">
                    Must contain readable text
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Column 2: Parameters */}
          <div className="space-y-4">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              2. Compliance Details
            </h2>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1.5">
                Product / Document Name
              </label>
              <input
                type="text"
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
                placeholder="e.g. Crispy Choco Chip Cookies"
                className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1.5">
                Primary Regulatory Compliance Area
              </label>
              <select
                value={complianceArea}
                onChange={(e) => setComplianceArea(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
              >
                {COMPLIANCE_AREAS.map((area) => (
                  <option key={area} value={area}>
                    {area}
                  </option>
                ))}
              </select>
              <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">
                Select the primary regulatory category for this check.
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1.5">
                Facility / Location Description (Optional)
              </label>
              <input
                type="text"
                value={facilityInfo}
                onChange={(e) => setFacilityInfo(e.target.value)}
                placeholder="e.g. Biscuit manufacturing facility in Maharashtra"
                className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex justify-end">
          <button
            type="submit"
            disabled={!file || isProcessing}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white font-semibold rounded-xl shadow-xs transition-colors cursor-pointer text-sm"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Checking Compliance...</span>
              </>
            ) : (
              <>
                <FileCheck2 className="w-4 h-4" />
                <span>Check Compliance</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
