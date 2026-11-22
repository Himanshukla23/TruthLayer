'use client';

import React, { useState } from 'react';
import {
  ShieldCheck,
  AlertTriangle,
  XCircle,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Calendar,
  Globe,
  Lightbulb,
} from 'lucide-react';
import { ClaimVerificationResult, VerificationStatus } from '@/types';

interface ClaimCardProps {
  claim: ClaimVerificationResult;
}

export default function ClaimCard({ claim }: ClaimCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const getStatusBadge = (status: VerificationStatus) => {
    switch (status) {
      case 'VERIFIED':
        return {
          icon: ShieldCheck,
          text: 'Verified',
          badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200/80',
          borderAccent: 'border-l-4 border-l-emerald-500',
        };
      case 'INACCURATE':
        return {
          icon: AlertTriangle,
          text: 'Inaccurate',
          badgeClass: 'bg-amber-50 text-amber-700 border-amber-200/80',
          borderAccent: 'border-l-4 border-l-amber-500',
        };
      case 'FALSE':
        return {
          icon: XCircle,
          text: 'False',
          badgeClass: 'bg-rose-50 text-rose-700 border-rose-200/80',
          borderAccent: 'border-l-4 border-l-rose-500',
        };
      case 'UNVERIFIED':
      default:
        return {
          icon: HelpCircle,
          text: 'Unverified',
          badgeClass: 'bg-slate-100 text-slate-700 border-slate-200',
          borderAccent: 'border-l-4 border-l-slate-400',
        };
    }
  };

  const statusConfig = getStatusBadge(claim.status);
  const StatusIcon = statusConfig.icon;
  const confPct = Math.round(claim.confidence * 100);

  return (
    <div
      className={`p-5 rounded-2xl bg-white border border-slate-200/90 shadow-xs hover:shadow-md transition-all ${statusConfig.borderAccent}`}
    >
      {/* Header Badges */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[11px] font-bold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-md">
            Page {claim.page_number}
          </span>
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 bg-slate-50 px-2 py-0.5 rounded-md border border-slate-200/60">
            {claim.claim_type}
          </span>
          {confPct > 0 ? (
            <span className="text-[11px] font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-md border border-blue-100">
              {confPct}% Confidence
            </span>
          ) : (
            <span className="text-[11px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">
              No Web Evidence
            </span>
          )}
        </div>

        {/* Status Chip */}
        <span
          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${statusConfig.badgeClass}`}
        >
          <StatusIcon className="w-3.5 h-3.5" />
          {statusConfig.text}
        </span>
      </div>

      {/* Original Claim Text */}
      <h3 className="text-base font-bold text-slate-900 leading-snug mb-3">
        &ldquo;{claim.original_claim}&rdquo;
      </h3>

      {/* Verified Correction Box for Inaccurate or False claims */}
      {claim.corrected_information && (
        <div className="mb-3.5 p-3.5 rounded-xl bg-amber-50/70 border border-amber-200/80 text-amber-950 text-xs leading-relaxed flex items-start gap-2.5">
          <Lightbulb className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <strong className="text-amber-800 uppercase tracking-wide block text-[10px] mb-0.5">
              Verified Correction
            </strong>
            {claim.corrected_information}
          </div>
        </div>
      )}

      {/* Justification / Explanation */}
      <div className="text-xs text-slate-600 leading-relaxed mb-3">
        <strong className="text-slate-900 font-semibold">Evaluation:</strong>{' '}
        {claim.explanation}
      </div>

      {/* Sources Toggle Button */}
      {claim.sources && claim.sources.length > 0 && (
        <div className="pt-2 border-t border-slate-100">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center gap-1.5 py-1 transition-colors"
          >
            <span>
              {isExpanded ? 'Hide' : 'View'} {claim.sources.length} Verified Web{' '}
              {claim.sources.length === 1 ? 'Source' : 'Sources'}
            </span>
            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {/* Sources Dropdown */}
          {isExpanded && (
            <div className="mt-3 space-y-2.5">
              {claim.sources.map((src, sIdx) => {
                const isAuth =
                  ['.gov', '.edu', '.org', '.int'].some((tld) =>
                    src.source_domain.endsWith(tld)
                  ) ||
                  ['reuters.com', 'bloomberg.com', 'apnews.com', 'bbc.com', 'wsj.com'].includes(
                    src.source_domain
                  );

                return (
                  <div
                    key={sIdx}
                    className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <a
                        href={src.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-bold text-blue-600 hover:underline flex items-center gap-1 truncate"
                      >
                        {src.title || src.url}
                        <ExternalLink className="w-3 h-3 shrink-0" />
                      </a>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">
                        {src.evidence_type || 'Supporting'}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-[11px] text-slate-500">
                      <span
                        className={`inline-flex items-center gap-1 font-semibold px-1.5 py-0.5 rounded ${
                          isAuth
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}
                      >
                        <Globe className="w-3 h-3" />
                        {src.source_domain}
                      </span>
                      {src.publication_date && (
                        <span className="inline-flex items-center gap-1 text-slate-400">
                          <Calendar className="w-3 h-3" />
                          {src.publication_date}
                        </span>
                      )}
                    </div>

                    {src.content_snippet && (
                      <p className="text-slate-600 italic bg-white p-2 rounded-lg border border-slate-100 text-[11px] leading-relaxed">
                        &ldquo;{src.content_snippet}&rdquo;
                      </p>
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
}
