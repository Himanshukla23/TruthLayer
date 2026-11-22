'use client';

import React, { useState } from 'react';
import Navbar from '@/components/Navbar';
import Dropzone from '@/components/Dropzone';
import HowItWorks from '@/components/HowItWorks';
import Stepper from '@/components/Stepper';
import Scorecard from '@/components/Scorecard';
import ClaimCard from '@/components/ClaimCard';
import ClaimsViewer from '@/components/ClaimsViewer';
import StepByStepAnalysis from '@/components/StepByStepAnalysis';
import {
  VerificationReport,
  ClaimExtractionResponse,
  ClaimVerificationResult,
  ClaimEvidenceResult,
  PDFExtractionResult,
} from '@/types';
import { Search } from 'lucide-react';

const getApiBase = () => {
  if (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
    return 'http://127.0.0.1:8000';
  }
  return '';
};

async function runConcurrent<T, R>(
  items: T[],
  concurrency: number,
  task: (item: T, index: number) => Promise<R>,
  onProgress?: (completed: number, total: number) => void
): Promise<R[]> {
  const results: R[] = new Array(items.length);
  let cursor = 0;
  let completed = 0;

  const workers = Array.from({ length: Math.min(concurrency, items.length) }, async () => {
    while (cursor < items.length) {
      const idx = cursor++;
      try {
        results[idx] = await task(items[idx], idx);
      } catch (err) {
        console.error(`Task ${idx} error:`, err);
      } finally {
        completed++;
        onProgress?.(completed, items.length);
      }
    }
  });

  await Promise.all(workers);
  return results;
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'history' | 'settings'>('dashboard');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentStage, setCurrentStage] = useState(1);
  const [stageMessage, setStageMessage] = useState('Ready');

  // Mode: 'overview' | 'step_by_step'
  const [viewMode, setViewMode] = useState<'overview' | 'step_by_step'>('overview');
  const [activeStep, setActiveStep] = useState<number>(1);
  const [isRunningStep, setIsRunningStep] = useState<boolean>(false);

  // Step results
  const [pdfResult, setPdfResult] = useState<PDFExtractionResult | null>(null);
  const [claimsResult, setClaimsResult] = useState<ClaimExtractionResponse | null>(null);
  const [evidenceList, setEvidenceList] = useState<ClaimEvidenceResult[]>([]);
  const [report, setReport] = useState<VerificationReport | null>(null);

  const [history, setHistory] = useState<VerificationReport[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [isExporting, setIsExporting] = useState(false);

  const handleFileSelected = (file: File) => {
    setError(null);
    setReport(null);
    setPdfResult(null);
    setClaimsResult(null);
    setEvidenceList([]);
    setViewMode('overview');
    setActiveStep(1);

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only standard PDF (.pdf) documents are supported.');
      return;
    }
    if (file.size > 4 * 1024 * 1024) {
      setError('File exceeds maximum Vercel serverless upload limit of 4.0 MB.');
      return;
    }
    setSelectedFile(file);
  };

  const handleClearFile = () => {
    setSelectedFile(null);
    setReport(null);
    setPdfResult(null);
    setClaimsResult(null);
    setEvidenceList([]);
    setError(null);
    setIsAnalyzing(false);
    setViewMode('overview');
    setActiveStep(1);
  };

  // 1. FULL AUTOMATIC ANALYSIS
  const handleAnalyze = async () => {
    if (!selectedFile) return;

    setIsAnalyzing(true);
    setError(null);

    try {
      setCurrentStage(1);
      setStageMessage('Uploading and extracting PDF text (PyMuPDF)...');

      const formData = new FormData();
      formData.append('file', selectedFile);

      const extractRes = await fetch(`${getApiBase()}/api/py/extract-claims`, {
        method: 'POST',
        body: formData,
      });

      if (!extractRes.ok) {
        let errMessage = `Extraction failed with HTTP ${extractRes.status}`;
        try {
          const errData = await extractRes.json();
          if (errData && errData.detail) {
            errMessage = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
          }
        } catch {
          const text = await extractRes.text().catch(() => '');
          if (text) {
            errMessage = text.length > 250 ? text.slice(0, 250) + '...' : text;
          }
        }
        throw new Error(errMessage);
      }

      setCurrentStage(3);
      setStageMessage('Isolating factual assertions with Gemini 3.5 Flash...');
      const claimsData: ClaimExtractionResponse = await extractRes.json();
      setClaimsResult(claimsData);

      if (!claimsData.claims || claimsData.claims.length === 0) {
        if (claimsData.error_message) {
          throw new Error(claimsData.error_message);
        }
        const emptyReport: VerificationReport = {
          document_name: selectedFile.name,
          total_pages: 1,
          total_claims: 0,
          verified_count: 0,
          inaccurate_count: 0,
          false_count: 0,
          unverified_count: 0,
          results: [],
          processed_at: new Date().toISOString(),
        };
        setReport(emptyReport);
        setHistory((prev) => [emptyReport, ...prev]);
        setIsAnalyzing(false);
        return;
      }

      const totalClaims = claimsData.claims.length;
      setCurrentStage(4);
      setStageMessage(`Auditing ${totalClaims} factual claims in parallel...`);

      const verifiedResults: ClaimVerificationResult[] = await runConcurrent(
        claimsData.claims,
        4,
        async (claim) => {
          for (let attempt = 0; attempt < 2; attempt++) {
            try {
              const verifyRes = await fetch(`${getApiBase()}/api/py/verify-single-claim`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  claim,
                  document_name: selectedFile.name,
                }),
              });

              if (verifyRes.ok) {
                const data: ClaimVerificationResult = await verifyRes.json();
                return data;
              }

              if (attempt === 0) {
                await new Promise((r) => setTimeout(r, 600));
                continue;
              }
            } catch (err) {
              if (attempt === 0) {
                await new Promise((r) => setTimeout(r, 600));
                continue;
              }
            }
          }

          return {
            claim_id: claim.claim_id,
            original_claim: claim.original_claim,
            page_number: claim.page_number,
            claim_type: claim.claim_type,
            status: 'UNVERIFIED',
            confidence: 0.0,
            explanation: 'Verification reasoning failed due to connectivity error.',
            sources: [],
          };
        },
        (done, total) => {
          setStageMessage(
            `Auditing factual claims: ${done} of ${total} verified (${Math.round((done / total) * 100)}%)...`
          );
        }
      );

      setCurrentStage(6);
      setStageMessage('Preparing comprehensive verification report...');

      const verifiedCount = verifiedResults.filter((r) => r.status === 'VERIFIED').length;
      const inaccurateCount = verifiedResults.filter((r) => r.status === 'INACCURATE').length;
      const falseCount = verifiedResults.filter((r) => r.status === 'FALSE').length;
      const unverifiedCount = verifiedResults.filter((r) => r.status === 'UNVERIFIED').length;

      const finalReport: VerificationReport = {
        document_name: selectedFile.name,
        total_pages: Math.max(1, ...claimsData.claims.map((c) => c.page_number)),
        total_claims: verifiedResults.length,
        verified_count: verifiedCount,
        inaccurate_count: inaccurateCount,
        false_count: falseCount,
        unverified_count: unverifiedCount,
        results: verifiedResults,
        processed_at: new Date().toISOString(),
      };

      setReport(finalReport);
      setHistory((prev) => [finalReport, ...prev]);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'An error occurred during fact verification.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // 2. STEP-BY-STEP MODE TRIGGER
  const handleStartStepByStep = async () => {
    if (!selectedFile) return;
    setViewMode('step_by_step');
    setActiveStep(1);
    await executeStep(1);
  };

  // EXECUTE SPECIFIC STEP
  const executeStep = async (stepNum: number) => {
    if (!selectedFile) return;
    setIsRunningStep(true);
    setError(null);

    try {
      if (stepNum === 1) {
        // Step 1: Extract Text
        const formData = new FormData();
        formData.append('file', selectedFile);
        const res = await fetch(`${getApiBase()}/api/py/extract-text`, { method: 'POST', body: formData });
        if (!res.ok) throw new Error('Text extraction failed.');
        const data: PDFExtractionResult = await res.json();
        setPdfResult(data);
        setActiveStep(1);
      } else if (stepNum === 2) {
        // Step 2: Extract Claims
        const formData = new FormData();
        formData.append('file', selectedFile);
        const res = await fetch(`${getApiBase()}/api/py/extract-claims`, { method: 'POST', body: formData });
        if (!res.ok) throw new Error('Claim extraction failed.');
        const data: ClaimExtractionResponse = await res.json();
        setClaimsResult(data);
        setActiveStep(2);
      } else if (stepNum === 3) {
        // Step 3: Web Evidence Retrieval (Parallel)
        if (!claimsResult || claimsResult.claims.length === 0) {
          throw new Error('Please extract claims first (Step 2).');
        }
        const evList = await runConcurrent(
          claimsResult.claims,
          4,
          async (claim) => {
            const res = await fetch(`${getApiBase()}/api/py/search-claim-evidence`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(claim),
            });
            if (res.ok) {
              return (await res.json()) as ClaimEvidenceResult;
            }
            return null;
          }
        );
        setEvidenceList(evList.filter((x): x is ClaimEvidenceResult => x !== null));
        setActiveStep(3);
      } else if (stepNum === 4 || stepNum === 5) {
        // Step 4 & 5: Fact Verification (Parallel)
        if (!claimsResult || claimsResult.claims.length === 0) {
          throw new Error('Please extract claims first.');
        }
        const verifiedResults = await runConcurrent(
          claimsResult.claims,
          4,
          async (claim) => {
            const res = await fetch(`${getApiBase()}/api/py/verify-single-claim`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ claim, document_name: selectedFile.name }),
            });
            if (res.ok) {
              return (await res.json()) as ClaimVerificationResult;
            }
            return {
              claim_id: claim.claim_id,
              original_claim: claim.original_claim,
              page_number: claim.page_number,
              claim_type: claim.claim_type,
              status: 'UNVERIFIED',
              confidence: 0.0,
              explanation: 'Verification reasoning failed.',
              sources: [],
            } as ClaimVerificationResult;
          }
        );
        const verifiedCount = verifiedResults.filter((r) => r.status === 'VERIFIED').length;
        const inaccurateCount = verifiedResults.filter((r) => r.status === 'INACCURATE').length;
        const falseCount = verifiedResults.filter((r) => r.status === 'FALSE').length;
        const unverifiedCount = verifiedResults.filter((r) => r.status === 'UNVERIFIED').length;

        const finalReport: VerificationReport = {
          document_name: selectedFile.name,
          total_pages: Math.max(1, ...claimsResult.claims.map((c) => c.page_number)),
          total_claims: verifiedResults.length,
          verified_count: verifiedCount,
          inaccurate_count: inaccurateCount,
          false_count: falseCount,
          unverified_count: unverifiedCount,
          results: verifiedResults,
          processed_at: new Date().toISOString(),
        };
        setReport(finalReport);
        setHistory((prev) => [finalReport, ...prev]);
        setActiveStep(stepNum);
      }
    } catch (err: any) {
      setError(err.message || 'Step execution failed.');
    } finally {
      setIsRunningStep(false);
    }
  };

  const handleNextStep = async () => {
    const next = activeStep + 1;
    if (next <= 5) {
      await executeStep(next);
    }
  };

  // EXPORT HANDLER
  const handleExport = async (format: 'pdf' | 'markdown' | 'json') => {
    if (!report) return;
    setIsExporting(true);

    try {
      const res = await fetch(`${getApiBase()}/api/py/generate-report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          report,
          format,
        }),
      });

      if (!res.ok) throw new Error('Export generation failed.');

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const ext = format === 'pdf' ? 'pdf' : format === 'markdown' ? 'md' : 'json';
      const cleanName = report.document_name.replace('.pdf', '').replace(/ /g, '_');
      a.download = `${cleanName}_verification_audit.${ext}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      alert(`Export error: ${err.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  // FILTERED CLAIMS
  const filteredClaims = (report?.results || []).filter((c) => {
    const matchesStatus =
      filterStatus === 'ALL' || c.status.toUpperCase() === filterStatus.toUpperCase();
    const query = searchQuery.trim().toLowerCase();
    const matchesSearch =
      !query ||
      c.original_claim.toLowerCase().includes(query) ||
      c.explanation.toLowerCase().includes(query) ||
      (c.corrected_information && c.corrected_information.toLowerCase().includes(query));
    return matchesStatus && matchesSearch;
  });

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        historyCount={history.length}
      />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* TAB: DASHBOARD */}
        {activeTab === 'dashboard' && (
          <div>
            {!report && !isAnalyzing && viewMode === 'overview' && (
              <div className="text-center mb-10">
                <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-slate-900 mb-3">
                  Verify what&apos;s inside{' '}
                  <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                    your documents.
                  </span>
                </h1>
                <p className="text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
                  Upload a PDF and let TruthLayer identify, research and verify factual claims using
                  reliable sources.
                </p>
              </div>
            )}

            {/* Stepper while analyzing in full mode */}
            {isAnalyzing && (
              <Stepper
                currentStage={currentStage}
                stageMessage={stageMessage}
                documentName={selectedFile?.name || 'Document'}
              />
            )}

            {/* Step-by-Step Interactive Experience */}
            {viewMode === 'step_by_step' && (
              <StepByStepAnalysis
                documentName={selectedFile?.name || 'Document'}
                pdfResult={pdfResult}
                claimsResult={claimsResult}
                evidenceList={evidenceList}
                report={report}
                activeStep={activeStep}
                setActiveStep={(st) => {
                  setActiveStep(st);
                  if (
                    (st === 1 && !pdfResult) ||
                    (st === 2 && !claimsResult) ||
                    (st === 3 && evidenceList.length === 0) ||
                    (st >= 4 && !report)
                  ) {
                    executeStep(st);
                  }
                }}
                isRunningStep={isRunningStep}
                onExecuteNextStep={handleNextStep}
                onReset={handleClearFile}
                onExport={handleExport}
                isExporting={isExporting}
              />
            )}

            {/* Dropzone when not analyzing, no report, and in overview mode */}
            {!report && !isAnalyzing && viewMode === 'overview' && (
              <>
                <Dropzone
                  onFileSelected={handleFileSelected}
                  selectedFile={selectedFile}
                  onClearFile={handleClearFile}
                  onAnalyze={handleAnalyze}
                  onStepByStep={handleStartStepByStep}
                  isAnalyzing={isAnalyzing}
                  error={error}
                />
                <HowItWorks />
              </>
            )}

            {/* Full Results Dashboard */}
            {report && !isAnalyzing && viewMode === 'overview' && (
              <div className="space-y-8 animate-in fade-in duration-300">
                <Scorecard
                  report={report}
                  onReset={handleClearFile}
                  onExport={handleExport}
                  isExporting={isExporting}
                />

                {/* Filter and Search Bar */}
                <div className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-xs flex flex-col md:flex-row items-center justify-between gap-4">
                  <div className="flex flex-wrap items-center gap-1.5 w-full md:w-auto">
                    {[
                      { key: 'ALL', label: `All Claims (${report.total_claims})` },
                      { key: 'VERIFIED', label: `Verified (${report.verified_count})` },
                      { key: 'INACCURATE', label: `Inaccurate (${report.inaccurate_count})` },
                      { key: 'FALSE', label: `False (${report.false_count})` },
                      { key: 'UNVERIFIED', label: `Unverified (${report.unverified_count})` },
                    ].map((pill) => (
                      <button
                        key={pill.key}
                        onClick={() => setFilterStatus(pill.key)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${filterStatus === pill.key
                            ? 'bg-blue-600 text-white shadow-xs'
                            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                          }`}
                      >
                        {pill.label}
                      </button>
                    ))}
                  </div>

                  <div className="relative w-full md:w-72">
                    <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      placeholder="Search within claims..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                    />
                  </div>
                </div>

                {/* Claims Cards List */}
                <div className="space-y-4">
                  {filteredClaims.length === 0 ? (
                    <div className="p-12 text-center rounded-2xl bg-white border border-slate-200/80">
                      <p className="text-sm text-slate-500">No claims match the selected filter.</p>
                    </div>
                  ) : (
                    filteredClaims.map((claim) => (
                      <ClaimCard key={claim.claim_id} claim={claim} />
                    ))
                  )}
                </div>
                {/* Interactive Claims Viewer (Split Inspector, Compact List, or Cards) */}
                <ClaimsViewer claims={report.results} />
              </div>
            )}
          </div>
        )}

        {/* TAB: HISTORY */}
        {activeTab === 'history' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-extrabold text-slate-900">Analysis History</h2>
            {history.length === 0 ? (
              <div className="p-12 text-center rounded-2xl bg-white border border-slate-200 text-slate-500 text-sm">
                No analyses completed in this session yet. Upload a document on the Dashboard to get started.
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4">
                {history.map((h, idx) => (
                  <div
                    key={idx}
                    className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs flex items-center justify-between"
                  >
                    <div>
                      <h4 className="font-bold text-slate-900 text-base">{h.document_name}</h4>
                      <p className="text-xs text-slate-500 mt-1">
                        {h.total_claims} claims • {h.verified_count} verified • {h.inaccurate_count}{' '}
                        inaccurate
                      </p>
                    </div>
                    <button
                      onClick={() => {
                        setReport(h);
                        setViewMode('overview');
                        setActiveTab('dashboard');
                      }}
                      className="px-4 py-2 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-700 font-bold text-xs transition-colors"
                    >
                      View Report
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB: SETTINGS */}
        {activeTab === 'settings' && (
          <div className="space-y-6 max-w-2xl mx-auto">
            <h2 className="text-2xl font-extrabold text-slate-900">System & Engine Settings</h2>
            <div className="p-6 rounded-2xl bg-white border border-slate-200/90 shadow-xs space-y-4">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div>
                  <h4 className="font-bold text-slate-900 text-sm">Google Gemini API</h4>
                  <p className="text-xs text-slate-500">Primary empirical reasoning model</p>
                </div>
                <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                  gemini-3.5-flash (Connected)
                </span>
              </div>
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div>
                  <h4 className="font-bold text-slate-900 text-sm">Tavily Search API</h4>
                  <p className="text-xs text-slate-500">Live web evidence retrieval engine</p>
                </div>
                <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                  Live Internet (Connected)
                </span>
              </div>
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div>
                  <h4 className="font-bold text-slate-900 text-sm">Groq Fallback</h4>
                  <p className="text-xs text-slate-500">Secondary fallback model</p>
                </div>
                <span className="text-xs font-bold text-blue-700 bg-blue-50 px-2.5 py-1 rounded-full border border-blue-200">
                  qwen/qwen3.8-27b (Ready)
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-bold text-slate-900 text-sm">Vercel Serverless Protection</h4>
                  <p className="text-xs text-slate-500">Max payload 4.0 MB, step-by-step chunking</p>
                </div>
                <span className="text-xs font-bold text-blue-700 bg-blue-50 px-2.5 py-1 rounded-full border border-blue-200">
                  Enforced
                </span>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
