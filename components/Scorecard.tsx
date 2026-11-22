'use client';

import React from 'react';
import { Download, RefreshCw, FileText, Code2, ShieldCheck, AlertTriangle, XCircle, HelpCircle } from 'lucide-react';
import { VerificationReport } from '@/types';

interface ScorecardProps {
  report: VerificationReport;
  onReset: () => void;
  onExport: (format: 'pdf' | 'markdown' | 'json') => void;
  isExporting: boolean;
}

export default function Scorecard({ report, onReset, onExport, isExporting }: ScorecardProps) {
  const tot = Math.max(1, report.total_claims);
  const credibilityScore = Math.round((report.verified_count / tot) * 100);

  const pctVerified = ((report.verified_count / tot) * 100).toFixed(1);
  const pctInaccurate = ((report.inaccurate_count / tot) * 100).toFixed(1);
  const pctFalse = ((report.false_count / tot) * 100).toFixed(1);
  const pctUnverified = ((report.unverified_count / tot) * 100).toFixed(1);

  let gradeBadge = {
    text: 'High Credibility',
    color: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    barColor: 'bg-emerald-500',
  };
  if (credibilityScore < 50) {
    gradeBadge = {
      text: 'Low Credibility',
      color: 'bg-rose-50 text-rose-700 border-rose-200',
      barColor: 'bg-rose-500',
    };
  } else if (credibilityScore < 80) {
    gradeBadge = {
      text: 'Needs Review',
      color: 'bg-amber-50 text-amber-700 border-amber-200',
      barColor: 'bg-amber-500',
    };
  }

  return (
    <div className="w-full space-y-6">
      {/* Top Document Header & Quick Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-white border border-slate-200/90 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
              VERIFICATION AUDIT
            </span>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-xs text-slate-500">{report.total_pages} Page(s)</span>
          </div>
          <h2 className="text-xl font-extrabold text-slate-900 mt-1 truncate max-w-lg">
            {report.document_name}
          </h2>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => onExport('pdf')}
            disabled={isExporting}
            className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-sm flex items-center gap-1.5 transition-all disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            Download PDF Report
          </button>
          <button
            onClick={onReset}
            className="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs flex items-center gap-1.5 transition-all"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            New Analysis
          </button>
        </div>
      </div>

      {/* Writing & Document Credibility Score Card (parafactai.com) */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200/90 shadow-xs">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Writing & Document Credibility Score
          </span>
          <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${gradeBadge.color}`}>
            {gradeBadge.text}
          </span>
        </div>

        <div className="flex items-baseline gap-3 mb-3">
          <span className="text-4xl font-extrabold tracking-tight text-slate-900">
            {credibilityScore}%
          </span>
          <span className="text-xs font-medium text-slate-500">
            ({report.verified_count} of {report.total_claims} factual claims verified against live web sources)
          </span>
        </div>

        {/* Credibility progress bar */}
        <div className="w-full bg-slate-100 h-3 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ${gradeBadge.barColor}`}
            style={{ width: `${credibilityScore}%` }}
          />
        </div>
      </div>

      {/* 5 Executive Metric Cards (basebright.ai style) */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3.5">
        {/* Total */}
        <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-xs">
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">
            Total Claims
          </div>
          <div className="text-2xl font-black text-slate-900">{report.total_claims}</div>
          <div className="text-[11px] text-slate-400 mt-1">Identified by AI</div>
        </div>

        {/* Verified */}
        <div className="p-4 rounded-xl bg-white border border-emerald-200/70 shadow-xs">
          <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 flex items-center gap-1 mb-1">
            <ShieldCheck className="w-3.5 h-3.5" /> Verified
          </div>
          <div className="text-2xl font-black text-emerald-600">{report.verified_count}</div>
          <div className="text-[11px] text-emerald-600/80 mt-1">{pctVerified}% Supported</div>
        </div>

        {/* Inaccurate */}
        <div className="p-4 rounded-xl bg-white border border-amber-200/70 shadow-xs">
          <div className="text-[11px] font-bold uppercase tracking-wider text-amber-700 flex items-center gap-1 mb-1">
            <AlertTriangle className="w-3.5 h-3.5" /> Inaccurate
          </div>
          <div className="text-2xl font-black text-amber-600">{report.inaccurate_count}</div>
          <div className="text-[11px] text-amber-600/80 mt-1">{pctInaccurate}% Discrepancy</div>
        </div>

        {/* False */}
        <div className="p-4 rounded-xl bg-white border border-rose-200/70 shadow-xs">
          <div className="text-[11px] font-bold uppercase tracking-wider text-rose-700 flex items-center gap-1 mb-1">
            <XCircle className="w-3.5 h-3.5" /> False
          </div>
          <div className="text-2xl font-black text-rose-600">{report.false_count}</div>
          <div className="text-[11px] text-rose-600/80 mt-1">{pctFalse}% Refuted</div>
        </div>

        {/* Unverified */}
        <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-xs col-span-2 sm:col-span-1">
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1 mb-1">
            <HelpCircle className="w-3.5 h-3.5" /> Unverified
          </div>
          <div className="text-2xl font-black text-slate-600">{report.unverified_count}</div>
          <div className="text-[11px] text-slate-400 mt-1">{pctUnverified}% No Sources</div>
        </div>
      </div>

      {/* Visual Breakdown Bar */}
      <div className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-xs">
        <div className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">
          Claims Accuracy Distribution
        </div>
        <div className="w-full h-3 rounded-full overflow-hidden flex bg-slate-100 mb-3">
          <div style={{ width: `${pctVerified}%` }} className="bg-emerald-500 transition-all" title={`Verified: ${pctVerified}%`} />
          <div style={{ width: `${pctInaccurate}%` }} className="bg-amber-500 transition-all" title={`Inaccurate: ${pctInaccurate}%`} />
          <div style={{ width: `${pctFalse}%` }} className="bg-rose-500 transition-all" title={`False: ${pctFalse}%`} />
          <div style={{ width: `${pctUnverified}%` }} className="bg-slate-400 transition-all" title={`Unverified: ${pctUnverified}%`} />
        </div>

        <div className="flex flex-wrap items-center gap-4 text-xs font-semibold text-slate-600">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            Verified ({report.verified_count} • {pctVerified}%)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            Inaccurate ({report.inaccurate_count} • {pctInaccurate}%)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
            False ({report.false_count} • {pctFalse}%)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-slate-400" />
            Unverified ({report.unverified_count} • {pctUnverified}%)
          </span>
        </div>
      </div>

      {/* Export Options */}
      <div className="flex flex-wrap items-center gap-3 pt-2">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-600">
          Export Document:
        </span>
        <button
          onClick={() => onExport('pdf')}
          disabled={isExporting}
          className="px-3.5 py-1.5 rounded-lg bg-white border border-slate-200 hover:border-slate-300 text-xs font-semibold text-slate-700 flex items-center gap-1.5 shadow-xs transition-colors"
        >
          <FileText className="w-3.5 h-3.5 text-rose-500" />
          PDF Audit Certificate
        </button>
        <button
          onClick={() => onExport('markdown')}
          disabled={isExporting}
          className="px-3.5 py-1.5 rounded-lg bg-white border border-slate-200 hover:border-slate-300 text-xs font-semibold text-slate-700 flex items-center gap-1.5 shadow-xs transition-colors"
        >
          <FileText className="w-3.5 h-3.5 text-blue-500" />
          Markdown Summary (.md)
        </button>
        <button
          onClick={() => onExport('json')}
          disabled={isExporting}
          className="px-3.5 py-1.5 rounded-lg bg-white border border-slate-200 hover:border-slate-300 text-xs font-semibold text-slate-700 flex items-center gap-1.5 shadow-xs transition-colors"
        >
          <Code2 className="w-3.5 h-3.5 text-amber-500" />
          JSON Data Certificate (.json)
        </button>
      </div>
    </div>
  );
}
