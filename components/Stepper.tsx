'use client';

import React from 'react';
import { Loader2, CheckCircle2, Circle } from 'lucide-react';

interface StepperProps {
  currentStage: number; // 1 to 6
  stageMessage: string;
  documentName: string;
}

export default function Stepper({ currentStage, stageMessage, documentName }: StepperProps) {
  const stages = [
    { num: 1, label: 'Uploading & validating document' },
    { num: 2, label: 'Extracting PDF text (PyMuPDF)' },
    { num: 3, label: 'Identifying factual claims (Gemini)' },
    { num: 4, label: 'Searching reliable sources (Tavily)' },
    { num: 5, label: 'Evaluating evidence & reasoning' },
    { num: 6, label: 'Preparing verification report' },
  ];

  const progressPercent = Math.min(100, Math.round((currentStage / 6) * 100));

  return (
    <div className="w-full max-w-xl mx-auto my-12 p-8 bg-white border border-slate-200/90 rounded-3xl shadow-sm text-center">
      <div className="w-12 h-12 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 mx-auto mb-4">
        <Loader2 className="w-6 h-6 animate-spin" />
      </div>

      <h3 className="text-xl font-bold text-slate-900 mb-1.5">
        Auditing Factual Claims...
      </h3>
      <p className="text-sm text-slate-500 mb-6 truncate max-w-md mx-auto">
        Analyzing <span className="font-semibold text-slate-700">{documentName}</span>
      </p>

      {/* Progress Bar */}
      <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden mb-6">
        <div
          className="bg-gradient-to-r from-blue-600 to-indigo-600 h-full rounded-full transition-all duration-500"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Current stage text */}
      <div className="text-xs font-semibold text-blue-700 bg-blue-50 px-3 py-1.5 rounded-lg border border-blue-100 inline-block mb-6">
        {stageMessage}
      </div>

      {/* Stepper items list */}
      <div className="space-y-2 text-left max-w-md mx-auto">
        {stages.map((st) => {
          const isDone = st.num < currentStage;
          const isCurrent = st.num === currentStage;

          return (
            <div
              key={st.num}
              className={`flex items-center gap-3 p-2.5 rounded-xl border text-xs font-medium transition-all ${
                isCurrent
                  ? 'bg-blue-50/70 border-blue-200 text-blue-900 font-bold'
                  : isDone
                  ? 'bg-slate-50 border-slate-200/60 text-slate-500'
                  : 'bg-transparent border-transparent text-slate-400'
              }`}
            >
              {isDone ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
              ) : isCurrent ? (
                <Loader2 className="w-4 h-4 text-blue-600 animate-spin shrink-0" />
              ) : (
                <Circle className="w-4 h-4 text-slate-300 shrink-0" />
              )}
              <span className="flex-1">{st.label}</span>
              {isDone && <span className="text-[10px] text-emerald-600 font-bold">Done</span>}
              {isCurrent && <span className="text-[10px] text-blue-600 font-bold">Running</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
}
