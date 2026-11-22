'use client';

import React, { useRef, useState } from 'react';
import { UploadCloud, FileText, X, Sparkles, AlertCircle } from 'lucide-react';

interface DropzoneProps {
  onFileSelected: (file: File) => void;
  selectedFile: File | null;
  onClearFile: () => void;
  onAnalyze: () => void;
  onStepByStep: () => void;
  isAnalyzing: boolean;
  error: string | null;
}

export default function Dropzone({
  onFileSelected,
  selectedFile,
  onClearFile,
  onAnalyze,
  onStepByStep,
  isAnalyzing,
  error,
}: DropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
        onFileSelected(file);
      }
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      onFileSelected(file);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      {/* rundocs.ai style Dropzone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !selectedFile && fileInputRef.current?.click()}
        className={`relative rounded-3xl p-10 md:p-14 text-center transition-all cursor-pointer ${
          isDragging
            ? 'bg-blue-100/70 border-2 border-blue-600 scale-[1.01] shadow-xl shadow-blue-500/10'
            : 'bg-blue-50/40 hover:bg-blue-50/70 border-2 border-dashed border-blue-200 hover:border-blue-500 shadow-sm'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={handleInputChange}
          disabled={isAnalyzing}
        />

        {/* Circular Blue Upload Icon */}
        <div className="w-16 h-16 rounded-full bg-blue-600 text-white flex items-center justify-center mx-auto mb-5 shadow-lg shadow-blue-600/30 group-hover:scale-105 transition-transform">
          <UploadCloud className="w-8 h-8" />
        </div>

        <h3 className="text-2xl font-bold text-slate-900 mb-2 tracking-tight">
          Drop files here
        </h3>
        <p className="text-slate-600 text-sm max-w-md mx-auto mb-4 leading-relaxed">
          Get summaries, extracted factual claims, and live web verification with exact citations.
        </p>

        <span className="inline-block text-xs font-semibold text-blue-600 bg-white px-3 py-1.5 rounded-full border border-blue-200 shadow-xs hover:border-blue-400 transition-colors">
          Or click to browse
        </span>

        {/* Supported formats pills */}
        <div className="mt-8 flex items-center justify-center gap-2 text-xs text-slate-500">
          <span>Supported format:</span>
          <span className="px-2.5 py-0.5 rounded-md bg-blue-100 font-bold text-blue-700 text-[11px]">
            PDF
          </span>
          <span className="text-slate-400">•</span>
          <span>Max file size: <strong>4.0 MB</strong></span>
        </div>
      </div>

      {/* Validation Error Banner */}
      {error && (
        <div className="mt-4 p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3 text-rose-800 text-sm">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="flex-1 font-medium">{error}</div>
        </div>
      )}

      {/* Selected File Card & Analyze CTA */}
      {selectedFile && !error && (
        <div className="mt-6 p-5 rounded-2xl bg-white border border-slate-200/90 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3.5 w-full sm:w-auto">
            <div className="w-11 h-11 rounded-xl bg-rose-50 border border-rose-100 flex items-center justify-center text-rose-600 shrink-0">
              <FileText className="w-6 h-6" />
            </div>
            <div className="min-w-0">
              <div className="text-sm font-bold text-slate-900 truncate max-w-xs md:max-w-md">
                {selectedFile.name}
              </div>
              <div className="text-xs text-slate-500">
                {formatFileSize(selectedFile.size)} • Ready for Fact-Checking
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 w-full sm:w-auto justify-end">
            <button
              onClick={onClearFile}
              disabled={isAnalyzing}
              className="p-2.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl transition-colors disabled:opacity-50"
              title="Remove File"
            >
              <X className="w-5 h-5" />
            </button>
            <button
              onClick={onStepByStep}
              disabled={isAnalyzing}
              className="px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-xs transition-all flex items-center justify-center gap-1.5 disabled:opacity-50"
            >
              🔍 Step-by-Step Mode
            </button>
            <button
              onClick={onAnalyze}
              disabled={isAnalyzing}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 hover:from-blue-700 hover:to-indigo-800 text-white font-bold text-sm shadow-md shadow-blue-500/25 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              Full Analysis
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
