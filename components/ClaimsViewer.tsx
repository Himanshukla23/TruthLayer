'use client';

import React, { useState, useMemo } from 'react';
import {
  ShieldCheck,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Search,
  ExternalLink,
  Calendar,
  Globe,
  Lightbulb,
  Columns,
  ListFilter,
  LayoutGrid,
  ChevronRight,
  ChevronLeft,
  ChevronDown,
  ChevronUp,
  Maximize2,
  Minimize2,
} from 'lucide-react';
import { ClaimVerificationResult, VerificationStatus } from '@/types';
import ClaimCard from './ClaimCard';

interface ClaimsViewerProps {
  claims: ClaimVerificationResult[];
}

export default function ClaimsViewer({ claims }: ClaimsViewerProps) {
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [viewMode, setViewMode] = useState<'split' | 'compact' | 'cards'>('split');
  const [selectedClaimId, setSelectedClaimId] = useState<string>(
    claims.length > 0 ? claims[0].claim_id : ''
  );
  const [expandedRowIds, setExpandedRowIds] = useState<Set<string>>(new Set());

  // Filtered claims
  const filteredClaims = useMemo(() => {
    return claims.filter((claim) => {
      const matchesStatus =
        filterStatus === 'ALL' || claim.status === filterStatus;
      const matchesSearch =
        !searchQuery ||
        claim.original_claim.toLowerCase().includes(searchQuery.toLowerCase()) ||
        claim.explanation.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (claim.corrected_information &&
          claim.corrected_information.toLowerCase().includes(searchQuery.toLowerCase()));
      return matchesStatus && matchesSearch;
    });
  }, [claims, filterStatus, searchQuery]);

  // Keep selected claim valid
  const activeClaim = useMemo(() => {
    return (
      filteredClaims.find((c) => c.claim_id === selectedClaimId) ||
      filteredClaims[0] ||
      null
    );
  }, [filteredClaims, selectedClaimId]);

  const activeIndex = useMemo(() => {
    if (!activeClaim) return -1;
    return filteredClaims.findIndex((c) => c.claim_id === activeClaim.claim_id);
  }, [filteredClaims, activeClaim]);

  // Status helper
  const getStatusBadge = (status: VerificationStatus) => {
    switch (status) {
      case 'VERIFIED':
        return {
          icon: ShieldCheck,
          label: 'Verified',
          pillClass: 'bg-emerald-50 text-emerald-700 border-emerald-200/90',
          dotClass: 'bg-emerald-500',
          borderAccent: 'border-l-4 border-l-emerald-500',
        };
      case 'INACCURATE':
        return {
          icon: AlertTriangle,
          label: 'Inaccurate',
          pillClass: 'bg-amber-50 text-amber-700 border-amber-200/90',
          dotClass: 'bg-amber-500',
          borderAccent: 'border-l-4 border-l-amber-500',
        };
      case 'FALSE':
        return {
          icon: XCircle,
          label: 'False',
          pillClass: 'bg-rose-50 text-rose-700 border-rose-200/90',
          dotClass: 'bg-rose-500',
          borderAccent: 'border-l-4 border-l-rose-500',
        };
      case 'UNVERIFIED':
      default:
        return {
          icon: HelpCircle,
          label: 'Unverified',
          pillClass: 'bg-slate-100 text-slate-700 border-slate-200',
          dotClass: 'bg-slate-400',
          borderAccent: 'border-l-4 border-l-slate-400',
        };
    }
  };

  // Quick navigation in split mode
  const handleSelectPrev = () => {
    if (activeIndex > 0) {
      setSelectedClaimId(filteredClaims[activeIndex - 1].claim_id);
    }
  };

  const handleSelectNext = () => {
    if (activeIndex < filteredClaims.length - 1) {
      setSelectedClaimId(filteredClaims[activeIndex + 1].claim_id);
    }
  };

  const toggleRowExpanded = (id: string) => {
    setExpandedRowIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const expandAllRows = () => {
    setExpandedRowIds(new Set(filteredClaims.map((c) => c.claim_id)));
  };

  const collapseAllRows = () => {
    setExpandedRowIds(new Set());
  };

  const countByStatus = useMemo(() => {
    return {
      all: claims.length,
      verified: claims.filter((c) => c.status === 'VERIFIED').length,
      inaccurate: claims.filter((c) => c.status === 'INACCURATE').length,
      falseCount: claims.filter((c) => c.status === 'FALSE').length,
      unverified: claims.filter((c) => c.status === 'UNVERIFIED').length,
    };
  }, [claims]);

  return (
    <div className="space-y-4">
      {/* 1. TOP TOOLBAR: Status Filter Tabs + Search + View Mode Switcher */}
      <div className="p-4 rounded-2xl bg-white border border-slate-200/90 shadow-xs flex flex-col lg:flex-row items-center justify-between gap-4">
        {/* Left: Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5 w-full lg:w-auto">
          {[
            { key: 'ALL', label: 'All', count: countByStatus.all, color: 'text-slate-700' },
            { key: 'INACCURATE', label: 'Inaccurate', count: countByStatus.inaccurate, color: 'text-amber-700' },
            { key: 'FALSE', label: 'False', count: countByStatus.falseCount, color: 'text-rose-700' },
            { key: 'VERIFIED', label: 'Verified', count: countByStatus.verified, color: 'text-emerald-700' },
            { key: 'UNVERIFIED', label: 'Unverified', count: countByStatus.unverified, color: 'text-slate-600' },
          ].map((pill) => (
            <button
              key={pill.key}
              onClick={() => {
                setFilterStatus(pill.key);
                if (filteredClaims.length > 0) {
                  setSelectedClaimId(filteredClaims[0].claim_id);
                }
              }}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                filterStatus === pill.key
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200/60'
              }`}
            >
              <span>{pill.label}</span>
              <span
                className={`text-[10px] px-1.5 py-0.2 rounded-full font-extrabold ${
                  filterStatus === pill.key
                    ? 'bg-white/20 text-white'
                    : 'bg-slate-200/70 text-slate-700'
                }`}
              >
                {pill.count}
              </span>
            </button>
          ))}
        </div>

        {/* Right: Search & View Mode Switcher */}
        <div className="flex items-center gap-3 w-full lg:w-auto justify-between lg:justify-end">
          {/* Search Box */}
          <div className="relative flex-1 lg:w-64">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search claims & facts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-slate-50 border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all placeholder:text-slate-400"
            />
          </div>

          {/* View Mode Toggle */}
          <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200 shrink-0">
            <button
              onClick={() => setViewMode('split')}
              title="Split Inspector View (Zero Scrolling)"
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                viewMode === 'split'
                  ? 'bg-white text-blue-600 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Columns className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Split Inspector</span>
            </button>

            <button
              onClick={() => setViewMode('compact')}
              title="Compact Dense List View"
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                viewMode === 'compact'
                  ? 'bg-white text-blue-600 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <ListFilter className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Compact List</span>
            </button>

            <button
              onClick={() => setViewMode('cards')}
              title="Card View"
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                viewMode === 'cards'
                  ? 'bg-white text-blue-600 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Cards</span>
            </button>
          </div>
        </div>
      </div>

      {/* 2. MAIN CONTENT AREA */}
      {filteredClaims.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-white border border-slate-200/80 shadow-xs">
          <p className="text-sm text-slate-500">No claims match the selected filter criteria.</p>
        </div>
      ) : viewMode === 'split' ? (
        /* ================= MODE A: SPLIT INSPECTOR VIEW (ZERO ENDLESS SCROLLING) ================= */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
          {/* Left Column: Bounded, Scrollable Claims Feed (5 cols) */}
          <div className="lg:col-span-5 bg-white border border-slate-200/90 rounded-2xl p-3 shadow-xs flex flex-col h-[650px]">
            <div className="flex items-center justify-between pb-2.5 mb-2 border-b border-slate-100 text-xs font-bold text-slate-500 px-2">
              <span>Claims Feed ({filteredClaims.length})</span>
              <span>Click to inspect</span>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
              {filteredClaims.map((claim, idx) => {
                const status = getStatusBadge(claim.status);
                const isSelected = activeClaim?.claim_id === claim.claim_id;
                const conf = Math.round(claim.confidence * 100);

                return (
                  <div
                    key={claim.claim_id}
                    onClick={() => setSelectedClaimId(claim.claim_id)}
                    className={`p-3 rounded-xl border text-left cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-blue-50/70 border-blue-400/80 shadow-xs ring-1 ring-blue-400'
                        : 'bg-white hover:bg-slate-50/80 border-slate-200/70'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-1.5 mb-1.5">
                      <div className="flex items-center gap-1.5">
                        <span className="text-[10px] font-extrabold text-slate-700 bg-slate-100 px-1.5 py-0.5 rounded">
                          {claim.claim_id}
                        </span>
                        <span className="text-[10px] font-semibold text-slate-500">
                          Pg {claim.page_number}
                        </span>
                      </div>

                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full border inline-flex items-center gap-1 ${status.pillClass}`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${status.dotClass}`} />
                        {status.label}
                      </span>
                    </div>

                    <p className="text-xs font-semibold text-slate-900 line-clamp-2 leading-relaxed">
                      &ldquo;{claim.original_claim}&rdquo;
                    </p>

                    <div className="flex items-center justify-between mt-2 pt-1.5 border-t border-slate-100/80 text-[10px] text-slate-500">
                      <span>{claim.claim_type}</span>
                      <span>{conf > 0 ? `${conf}% confidence` : 'No sources'}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Sticky Detailed Inspection Panel (7 cols) */}
          <div className="lg:col-span-7 bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs h-[650px] flex flex-col sticky top-4">
            {activeClaim ? (
              <>
                {/* Header & Prev/Next Controls */}
                <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-extrabold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-md border border-blue-100">
                      {activeClaim.claim_id}
                    </span>
                    <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">
                      Page {activeClaim.page_number}
                    </span>
                    <span className="text-xs font-medium text-slate-500">
                      {activeClaim.claim_type}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-slate-400">
                      {activeIndex + 1} of {filteredClaims.length}
                    </span>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={handleSelectPrev}
                        disabled={activeIndex <= 0}
                        title="Previous Claim"
                        className="p-1.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 disabled:opacity-30 transition-all"
                      >
                        <ChevronLeft className="w-3.5 h-3.5 text-slate-700" />
                      </button>
                      <button
                        onClick={handleSelectNext}
                        disabled={activeIndex >= filteredClaims.length - 1}
                        title="Next Claim"
                        className="p-1.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 disabled:opacity-30 transition-all"
                      >
                        <ChevronRight className="w-3.5 h-3.5 text-slate-700" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Scrollable Inspector Body */}
                <div className="flex-1 overflow-y-auto space-y-4 pt-4 pr-1 custom-scrollbar">
                  {/* Status Banner */}
                  {(() => {
                    const st = getStatusBadge(activeClaim.status);
                    const StatusIcon = st.icon;
                    return (
                      <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
                        <div className="flex items-center gap-2.5">
                          <span
                            className={`p-2 rounded-lg border ${st.pillClass}`}
                          >
                            <StatusIcon className="w-5 h-5" />
                          </span>
                          <div>
                            <span className="text-xs font-bold text-slate-900 block">
                              Veracity Verdict: {st.label}
                            </span>
                            <span className="text-[11px] text-slate-500">
                              Based on corroborated web evidence
                            </span>
                          </div>
                        </div>

                        <div className="text-right">
                          <span className="text-sm font-extrabold text-slate-900">
                            {Math.round(activeClaim.confidence * 100)}%
                          </span>
                          <span className="text-[10px] text-slate-400 block">
                            Confidence Score
                          </span>
                        </div>
                      </div>
                    );
                  })()}

                  {/* Original Claim Assertion */}
                  <div>
                    <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                      Original Document Claim
                    </h4>
                    <div className="p-3.5 rounded-xl bg-slate-900 text-white font-medium text-sm leading-relaxed">
                      &ldquo;{activeClaim.original_claim}&rdquo;
                    </div>
                  </div>

                  {/* Verified Correction Box (if inaccurate or false) */}
                  {activeClaim.corrected_information && (
                    <div className="p-4 rounded-xl bg-amber-50/80 border border-amber-300 text-amber-950 text-xs leading-relaxed space-y-1">
                      <div className="flex items-center gap-1.5 font-bold text-amber-800 uppercase tracking-wide text-[10px]">
                        <Lightbulb className="w-3.5 h-3.5 text-amber-600" />
                        Verified Correction
                      </div>
                      <p className="font-semibold text-slate-900">
                        {activeClaim.corrected_information}
                      </p>
                    </div>
                  )}

                  {/* AI Evaluation Reasoning */}
                  <div>
                    <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                      Evidence Evaluation & Provenance Reasoning
                    </h4>
                    <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-3 rounded-xl border border-slate-200/70">
                      {activeClaim.explanation}
                    </p>
                  </div>

                  {/* Verified Sources */}
                  <div>
                    <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">
                      Cited Primary & Secondary Web Sources ({activeClaim.sources?.length || 0})
                    </h4>

                    {!activeClaim.sources || activeClaim.sources.length === 0 ? (
                      <p className="text-xs text-slate-400 italic">No external web citations linked.</p>
                    ) : (
                      <div className="space-y-2">
                        {activeClaim.sources.map((src, sIdx) => (
                          <div
                            key={sIdx}
                            className="p-3 rounded-xl bg-white border border-slate-200 shadow-2xs text-xs space-y-1.5"
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
                              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                                {src.evidence_type || 'Supporting'}
                              </span>
                            </div>

                            <div className="flex items-center gap-2 text-[11px] text-slate-500">
                              <span className="inline-flex items-center gap-1 font-semibold text-emerald-800 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
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
                              <p className="text-slate-600 italic bg-slate-50 p-2 rounded-lg border border-slate-100 text-[11px] leading-relaxed">
                                &ldquo;{src.content_snippet}&rdquo;
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400 text-xs">
                Select a claim from the feed to view full verification details.
              </div>
            )}
          </div>
        </div>
      ) : viewMode === 'compact' ? (
        /* ================= MODE B: COMPACT DENSE TABLE / ACCORDION ================= */
        <div className="bg-white border border-slate-200/90 rounded-2xl shadow-xs overflow-hidden">
          {/* Header Controls */}
          <div className="p-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between text-xs">
            <span className="font-bold text-slate-700">
              Showing {filteredClaims.length} Claims
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={expandAllRows}
                className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
              >
                <Maximize2 className="w-3.5 h-3.5" />
                Expand All
              </button>
              <span className="text-slate-300">|</span>
              <button
                onClick={collapseAllRows}
                className="text-xs font-semibold text-slate-600 hover:text-slate-700 flex items-center gap-1"
              >
                <Minimize2 className="w-3.5 h-3.5" />
                Collapse All
              </button>
            </div>
          </div>

          {/* Dense Rows */}
          <div className="divide-y divide-slate-100">
            {filteredClaims.map((claim) => {
              const status = getStatusBadge(claim.status);
              const isExpanded = expandedRowIds.has(claim.claim_id);
              const conf = Math.round(claim.confidence * 100);

              return (
                <div key={claim.claim_id} className="transition-all">
                  {/* Dense Row Header */}
                  <div
                    onClick={() => toggleRowExpanded(claim.claim_id)}
                    className="p-3.5 flex items-center gap-3 cursor-pointer hover:bg-slate-50/80 transition-colors"
                  >
                    <button className="text-slate-400 hover:text-slate-600">
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )}
                    </button>

                    <span className="text-[11px] font-extrabold text-slate-700 bg-slate-100 px-2 py-0.5 rounded shrink-0">
                      {claim.claim_id}
                    </span>

                    <span className="text-[11px] font-semibold text-slate-500 shrink-0">
                      Pg {claim.page_number}
                    </span>

                    <p className="text-xs font-bold text-slate-900 truncate flex-1">
                      &ldquo;{claim.original_claim}&rdquo;
                    </p>

                    <div className="flex items-center gap-2 shrink-0">
                      <span
                        className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border inline-flex items-center gap-1.5 ${status.pillClass}`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${status.dotClass}`} />
                        {status.label}
                      </span>
                      <span className="text-[11px] font-semibold text-slate-500 w-12 text-right hidden sm:inline">
                        {conf}%
                      </span>
                    </div>
                  </div>

                  {/* Expanded Row Detail */}
                  {isExpanded && (
                    <div className="p-4 bg-slate-50/60 border-t border-slate-100 space-y-3 pl-11">
                      {claim.corrected_information && (
                        <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs">
                          <strong className="text-amber-800 uppercase block text-[10px] mb-0.5">
                            Verified Correction
                          </strong>
                          {claim.corrected_information}
                        </div>
                      )}

                      <div className="text-xs text-slate-700">
                        <strong className="font-semibold text-slate-900">Evaluation:</strong>{' '}
                        {claim.explanation}
                      </div>

                      {claim.sources && claim.sources.length > 0 && (
                        <div className="flex flex-wrap gap-2 pt-1">
                          {claim.sources.map((s, idx) => (
                            <a
                              key={idx}
                              href={s.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-[11px] font-semibold text-blue-600 bg-white border border-slate-200 px-2 py-1 rounded-md hover:underline flex items-center gap-1 shadow-2xs"
                            >
                              <Globe className="w-3 h-3 text-emerald-600" />
                              {s.source_domain}
                              <ExternalLink className="w-2.5 h-2.5" />
                            </a>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        /* ================= MODE C: CLASSIC CARD VIEW ================= */
        <div className="space-y-4">
          {filteredClaims.map((claim) => (
            <ClaimCard key={claim.claim_id} claim={claim} />
          ))}
        </div>
      )}
    </div>
  );
}
