import React, { useState } from 'react';
import { complianceApi } from '../api';
import { SearchResultItem } from '../types';
import {
  Search,
  BookOpen,
  ChevronDown,
  ChevronUp,
  Loader2,
  AlertCircle,
  Sliders,
  CheckCircle,
} from 'lucide-react';

export const SearchRegulations: React.FC = () => {
  const [query, setQuery] = useState(
    'What mandatory labelling elements must appear on pre-packaged food containers?'
  );
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResultItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Expanded items
  const [expandedIndices, setExpandedIndices] = useState<Record<number, boolean>>({ 0: true });

  const toggleExpand = (idx: number) => {
    setExpandedIndices((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) {
      setError('Please enter a search topic or question.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const resp = await complianceApi.searchRegulations(query.trim(), topK);
      const items = resp.data?.results || [];
      setResults(items);
      const initialExp: Record<number, boolean> = {};
      items.forEach((_, i) => {
        initialExp[i] = i === 0;
      });
      setExpandedIndices(initialExp);
    } catch (err: any) {
      setError(
        err.response?.data?.error ||
          'Unable to complete search. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 dark:text-white">
          Search Food Regulations
        </h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
          Look up specific requirements and guidelines from official food safety standards.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-rose-600" />
          <div className="flex-1">{error}</div>
        </div>
      )}

      {/* Search Input Box */}
      <form
        onSubmit={handleSearch}
        className="bg-white dark:bg-[#111827] rounded-2xl border border-slate-200 dark:border-slate-800 p-6 md:p-8 shadow-sm space-y-5"
      >
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
            Search regulatory requirements or topics:
          </label>
          <div className="relative">
            <Search className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. maximum permissible pesticide residues in tea..."
              className="w-full pl-11 pr-4 py-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>
        </div>

        {/* Top K slider */}
        <div className="pt-2">
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-slate-400" />
              <span>Maximum results:</span>
            </label>
            <span className="text-xs font-mono font-bold px-2 py-0.5 bg-slate-100 dark:bg-slate-800 rounded text-slate-700 dark:text-slate-300">
              {topK} results
            </span>
          </div>
          <input
            type="range"
            min={1}
            max={10}
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            className="w-full accent-sky-600 cursor-pointer"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-sky-600 hover:bg-sky-500 disabled:opacity-60 text-white font-semibold text-sm rounded-xl shadow-xs transition-colors cursor-pointer"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Searching regulations...</span>
            </>
          ) : (
            <>
              <Search className="w-4 h-4" />
              <span>Search Regulations</span>
            </>
          )}
        </button>
      </form>

      {/* Results */}
      {results !== null && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-emerald-700 dark:text-emerald-400 font-semibold bg-emerald-50 dark:bg-emerald-950/40 p-3.5 rounded-xl border border-emerald-200 dark:border-emerald-900">
            <CheckCircle className="w-4 h-4" />
            <span>Found {results.length} matching regulations:</span>
          </div>

          {results.length === 0 ? (
            <div className="p-8 text-center bg-white dark:bg-[#111827] rounded-xl border border-slate-200 dark:border-slate-800 text-slate-500">
              No matching regulations found for this query. Try different keywords.
            </div>
          ) : (
            <div className="space-y-3">
              {results.map((r, idx) => {
                const docTitle = r.doc_title || r.doc_filename || 'Regulatory Standard';
                const pages = r.page_start ? `Pages ${r.page_start}–${r.page_end}` : '';
                const sec = r.section_title ? ` | Section: ${r.section_title}` : '';
                const isExpanded = !!expandedIndices[idx];

                return (
                  <div
                    key={idx}
                    className="bg-white dark:bg-[#111827] rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-xs"
                  >
                    <button
                      type="button"
                      onClick={() => toggleExpand(idx)}
                      className="w-full p-4 flex items-center justify-between text-left hover:bg-slate-50 dark:hover:bg-slate-900/40 transition-colors cursor-pointer"
                    >
                      <div className="flex items-center gap-3 pr-4">
                        <div className="w-7 h-7 rounded-lg bg-sky-50 dark:bg-sky-950/60 text-sky-600 dark:text-sky-400 font-bold text-xs flex items-center justify-center shrink-0">
                          {idx + 1}
                        </div>
                        <div>
                          <h3 className="font-semibold text-sm text-slate-900 dark:text-white flex items-center gap-1.5 flex-wrap">
                            <span>{docTitle}</span>
                            {(pages || sec) && (
                              <span className="text-xs font-normal text-slate-500 dark:text-slate-400">
                                ({pages}
                                {sec})
                              </span>
                            )}
                          </h3>
                        </div>
                      </div>
                      <div>
                        {isExpanded ? (
                          <ChevronUp className="w-5 h-5 text-slate-400" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-slate-400" />
                        )}
                      </div>
                    </button>

                    {isExpanded && (
                      <div className="px-5 pb-5 pt-2 border-t border-slate-100 dark:border-slate-800 text-sm">
                        <div className="bg-slate-50 dark:bg-slate-900/60 p-4 rounded-lg font-mono text-xs text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed border border-slate-200/50 dark:border-slate-800">
                          {r.content}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
