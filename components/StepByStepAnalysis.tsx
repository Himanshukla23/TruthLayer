'use client';

import React, { useState } from 'react';
import {
  FileText,
  Search,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Globe,
  ExternalLink,
  ChevronRight,
  ArrowRight,
  RefreshCw,
  Sparkles,
  Download,
  Lightbulb,
} from 'lucide-react';
import {
  PDFExtractionResult,
  ClaimExtractionResponse,
  ClaimEvidenceResult,
  ClaimVerificationResult,
  VerificationReport,
  ExtractedClaimItem,
} from '@/types';
import Scorecard from '@/components/Scorecard';
import ClaimCard from '@/components/ClaimCard';

interface StepByStepAnalysisProps {
  documentName: string;
  pdfResult: PDFExtractionResult | null;
  claimsResult: ClaimExtractionResponse | null;
  evidenceList: ClaimEvidenceResult[];
  report: VerificationReport | null;
  activeStep: number;
  setActiveStep: (step: number) => void;
  isRunningStep: boolean;
  onExecuteNextStep: () => void;
  onReset: () => void;
  onExport: (format: 'pdf' | 'markdown' | 'json') => void;
  isExporting: boolean;
}

export default function StepByStepAnalysis({
  documentName,
  pdfResult,
  claimsResult,
  evidenceList,
  report,
  activeStep,
  setActiveStep,
  isRunningStep,
  onExecuteNextStep,
  onReset,
  onExport,
  isExporting,
}: StepByStepAnalysisProps) {
  const [selectedPageNum, setSelectedPageNum] = useState<number>(1);
  const [selectedClaimId, setSelectedClaimId] = useState<string>('');

  const steps = [
    { num: 1, title: 'PDF Parsing', subtitle: 'PyMuPDF Text Extraction' },
    { num: 2, title: 'Claim Isolation', subtitle: 'Gemini 3.5 Flash' },
    { num: 3, title: 'Web Evidence', subtitle: 'Tavily Search API' },
    { num: 4, title: 'Fact Verification', subtitle: 'AI Reasoning Engine' },
    { num: 5, title: 'Audit Report', subtitle: 'Final Scorecard & Export' },
  ];

  return (
    <div className="w-full space-y-6 animate-in fade-in duration-300">
      {/* Top Header & Reset */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-white border border-slate-200/90 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
              STEP-BY-STEP VERIFICATION
            </span>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-xs text-slate-500">{documentName}</span>
          </div>
          <h2 className="text-xl font-extrabold text-slate-900 mt-1">
            Step {activeStep} of 5: {steps[activeStep - 1]?.title}
          </h2>
        </div>

        <div className="flex items-center gap-2.5">
          {activeStep < 5 && (
            <button
              onClick={onExecuteNextStep}
              disabled={isRunningStep}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold text-xs shadow-md shadow-blue-500/20 flex items-center gap-2 transition-all disabled:opacity-50"
            >
              {isRunningStep ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  Run Step {activeStep} ➔
                </>
              )}
            </button>
          )}

          <button
            onClick={onReset}
            className="px-3.5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs flex items-center gap-1.5 transition-all"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Reset
          </button>
        </div>
      </div>

      {/* Stepper Navigation Pills */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
        {steps.map((st) => {
          const isCurrent = activeStep === st.num;
          const isDone = activeStep > st.num || (st.num === 1 && pdfResult) || (st.num === 2 && claimsResult) || (st.num === 3 && evidenceList.length > 0) || (st.num === 4 && report) || (st.num === 5 && report);

          return (
            <button
              key={st.num}
              onClick={() => setActiveStep(st.num)}
              className={`p-3.5 rounded-xl border text-left transition-all ${
                isCurrent
                  ? 'bg-blue-600 text-white border-blue-600 shadow-md shadow-blue-500/20 ring-2 ring-blue-500/20'
                  : isDone
                  ? 'bg-white text-slate-800 border-slate-200 hover:border-blue-300'
                  : 'bg-slate-50 text-slate-400 border-slate-200/60'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span
                  className={`text-[10px] font-bold uppercase tracking-wider ${
                    isCurrent ? 'text-blue-100' : isDone ? 'text-blue-600' : 'text-slate-400'
                  }`}
                >
                  Step {st.num}
                </span>
                {isDone && !isCurrent && (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                )}
              </div>
              <div className={`text-xs font-bold truncate ${isCurrent ? 'text-white' : 'text-slate-900'}`}>
                {st.title}
              </div>
              <div
                className={`text-[10px] truncate mt-0.5 ${
                  isCurrent ? 'text-blue-100' : 'text-slate-500'
                }`}
              >
                {st.subtitle}
              </div>
            </button>
          );
        })}
      </div>

      {/* STEP 1: PDF PARSING VIEW */}
      {activeStep === 1 && (
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900">Extracted PDF Content</h3>
              <p className="text-xs text-slate-500">
                PyMuPDF extracted {pdfResult?.total_characters || 0} characters across{' '}
                {pdfResult?.total_pages || 0} pages.
              </p>
            </div>
            <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200">
              Extraction: {pdfResult?.extraction_status || 'Ready'}
            </span>
          </div>

          {pdfResult && pdfResult.pages.length > 0 ? (
            <div>
              {/* Page Selector Tabs */}
              <div className="flex flex-wrap gap-2 mb-4 pb-3 border-b border-slate-100">
                {pdfResult.pages.map((p) => (
                  <button
                    key={p.page_number}
                    onClick={() => setSelectedPageNum(p.page_number)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                      selectedPageNum === p.page_number
                        ? 'bg-blue-600 text-white shadow-xs'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    Page {p.page_number} ({p.character_count} chars)
                  </button>
                ))}
              </div>

              {/* Page Content Display */}
              {(() => {
                const currentPage = pdfResult.pages.find((p) => p.page_number === selectedPageNum) || pdfResult.pages[0];
                return (
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 font-mono text-xs leading-relaxed text-slate-800 whitespace-pre-wrap max-h-96 overflow-y-auto">
                    {currentPage.text || '[Empty Page - No text found]'}
                  </div>
                );
              })()}
            </div>
          ) : (
            <div className="p-8 text-center text-slate-500 text-sm">
              No PDF text extracted yet. Click &quot;Run Step 1&quot; above.
            </div>
          )}
        </div>
      )}

      {/* STEP 2: CLAIM ISOLATION VIEW */}
      {activeStep === 2 && (
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900">
                AI Empirical Claim Extraction ({claimsResult?.total_claims || 0} Claims)
              </h3>
              <p className="text-xs text-slate-500">
                Gemini 3.5 Flash filtered promotional text and isolated verifiable empirical statements.
              </p>
            </div>
            <span className="text-xs font-bold text-blue-700 bg-blue-50 px-2.5 py-1 rounded-md border border-blue-200">
              Model: {claimsResult?.extraction_model_used || 'Gemini 3.5 Flash'}
            </span>
          </div>

          {claimsResult && claimsResult.claims.length > 0 ? (
            <div className="space-y-3">
              {claimsResult.claims.map((c) => (
                <div
                  key={c.claim_id}
                  className="p-4 rounded-xl bg-slate-50 border border-slate-200 hover:border-blue-300 text-xs space-y-2 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-blue-700 bg-blue-100 px-2 py-0.5 rounded">
                        {c.claim_id}
                      </span>
                      <span className="font-semibold text-slate-600 bg-white px-2 py-0.5 rounded border border-slate-200">
                        Page {c.page_number}
                      </span>
                      <span className="font-semibold uppercase tracking-wider text-slate-500">
                        {c.claim_type}
                      </span>
                    </div>
                  </div>

                  <p className="font-bold text-slate-900 text-sm">&ldquo;{c.original_claim}&rdquo;</p>

                  <div className="flex flex-wrap items-center gap-1.5 pt-1 text-[11px]">
                    {c.numbers.map((n, idx) => (
                      <span key={idx} className="bg-white px-2 py-0.5 rounded border border-slate-200 text-slate-600">
                        🔢 {n}
                      </span>
                    ))}
                    {c.dates.map((d, idx) => (
                      <span key={idx} className="bg-white px-2 py-0.5 rounded border border-slate-200 text-slate-600">
                        📅 {d}
                      </span>
                    ))}
                    {c.entities.map((e, idx) => (
                      <span key={idx} className="bg-white px-2 py-0.5 rounded border border-slate-200 text-slate-600">
                        🏷️ {e}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-slate-500 text-sm">
              Claims have not been extracted yet. Click &quot;Run Step 2&quot; above.
            </div>
          )}
        </div>
      )}

      {/* STEP 3: WEB EVIDENCE VIEW */}
      {activeStep === 3 && (
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-5">
          <div>
            <h3 className="text-base font-bold text-slate-900">
              Live Web Evidence Retrieval (Tavily Search API)
            </h3>
            <p className="text-xs text-slate-500">
              Gathered real-time evidence snippets and verified source links for each factual assertion.
            </p>
          </div>

          {evidenceList && evidenceList.length > 0 ? (
            <div className="space-y-4">
              {evidenceList.map((evItem) => (
                <div key={evItem.claim_id} className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-blue-700 bg-blue-100 px-2 py-0.5 rounded">
                      {evItem.claim_id}
                    </span>
                    <strong className="text-slate-900 truncate">&ldquo;{evItem.original_claim}&rdquo;</strong>
                  </div>

                  {/* Search Queries Used */}
                  <div className="space-y-1">
                    <div className="text-[11px] font-bold uppercase text-slate-500">Targeted Queries:</div>
                    <div className="flex flex-wrap gap-1.5">
                      {evItem.search_queries.map((q, qIdx) => (
                        <span key={qIdx} className="bg-white px-2 py-0.5 rounded border border-slate-200 text-slate-700 text-[11px]">
                          🔍 {q}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Evidence Snippets */}
                  <div className="space-y-2 pt-1">
                    <div className="text-[11px] font-bold uppercase text-slate-500">
                      Retrieved Sources ({evItem.evidence.length}):
                    </div>
                    {evItem.evidence.length === 0 ? (
                      <p className="text-slate-400 italic">No external web sources found for this claim.</p>
                    ) : (
                      evItem.evidence.map((snippet, sIdx) => (
                        <div key={sIdx} className="p-3 rounded-lg bg-white border border-slate-200/80 text-[11px] space-y-1">
                          <a
                            href={snippet.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-bold text-blue-600 hover:underline flex items-center gap-1"
                          >
                            {snippet.source_title}
                            <ExternalLink className="w-3 h-3" />
                          </a>
                          <span className="text-slate-400">🌐 {snippet.source_domain}</span>
                          <p className="text-slate-600 italic mt-1">&ldquo;{snippet.content_snippet}&rdquo;</p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-slate-500 text-sm">
              No live web evidence retrieved yet. Click &quot;Run Step 3&quot; above.
            </div>
          )}
        </div>
      )}

      {/* STEP 4: FACT VERIFICATION VIEW */}
      {activeStep === 4 && (
        <div className="space-y-4">
          <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs">
            <h3 className="text-base font-bold text-slate-900">
              AI Fact Verification Reasoning & Verdicts
            </h3>
            <p className="text-xs text-slate-500">
              Comparing extracted assertions with live web evidence snippets.
            </p>
          </div>

          {report && report.results.length > 0 ? (
            <div className="space-y-4">
              {report.results.map((c) => (
                <ClaimCard key={c.claim_id} claim={c} />
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-slate-500 text-sm rounded-2xl bg-white border border-slate-200">
              Verifications have not completed yet. Click &quot;Run Step 4&quot; above.
            </div>
          )}
        </div>
      )}

      {/* STEP 5: FINAL AUDIT REPORT */}
      {activeStep === 5 && (
        <div className="space-y-6">
          {report ? (
            <>
              <Scorecard
                report={report}
                onReset={onReset}
                onExport={onExport}
                isExporting={isExporting}
              />
              <div className="space-y-4">
                {report.results.map((c) => (
                  <ClaimCard key={c.claim_id} claim={c} />
                ))}
              </div>
            </>
          ) : (
            <div className="p-8 text-center text-slate-500 text-sm rounded-2xl bg-white border border-slate-200">
              Complete the verification steps above to generate your final audit certificate.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
