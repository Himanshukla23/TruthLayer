'use client';

import React from 'react';
import { Cpu, Zap, Globe, Shield } from 'lucide-react';

export default function HowItWorks() {
  const steps = [
    {
      step: 'Step 1',
      title: 'AI Processing',
      desc: 'Automatic extraction of text, layout entities and metadata page-by-page using PyMuPDF.',
      icon: Cpu,
      color: 'bg-purple-50 text-purple-600 border-purple-100',
    },
    {
      step: 'Step 2',
      title: 'Fast & Efficient',
      desc: 'Gemini 2.5 Flash isolates empirical assertions, statistics, numbers and dates while filtering opinions.',
      icon: Zap,
      color: 'bg-amber-50 text-amber-600 border-amber-100',
    },
    {
      step: 'Step 3',
      title: 'Live Web Search',
      desc: 'Tavily Search API executes multi-angle live web queries across authoritative institutional domains.',
      icon: Globe,
      color: 'bg-blue-50 text-blue-600 border-blue-100',
    },
    {
      step: 'Step 4',
      title: 'Maximum Security',
      desc: 'Evidence synthesis delivers transparent verdicts, verified corrections and downloadable audit reports.',
      icon: Shield,
      color: 'bg-emerald-50 text-emerald-600 border-emerald-100',
    },
  ];

  return (
    <div className="w-full max-w-5xl mx-auto mt-16 pt-10 border-t border-slate-200/80">
      <div className="text-center mb-8">
        <span className="text-xs font-bold uppercase tracking-widest text-slate-600">
          WHAT HAPPENS TO YOUR DOCUMENTS
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {steps.map((s, idx) => {
          const Icon = s.icon;
          return (
            <div
              key={idx}
              className="p-5 rounded-2xl bg-white border border-slate-200/80 hover:border-blue-200 shadow-xs hover:shadow-md hover:-translate-y-0.5 transition-all"
            >
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 border ${s.color}`}
              >
                <Icon className="w-5 h-5" />
              </div>
              <div className="text-[11px] font-bold text-blue-600 uppercase tracking-wider mb-1">
                {s.step}
              </div>
              <h4 className="text-base font-bold text-slate-900 mb-1.5">{s.title}</h4>
              <p className="text-xs text-slate-500 leading-relaxed">{s.desc}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
