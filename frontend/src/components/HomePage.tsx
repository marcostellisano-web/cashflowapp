import { useCallback, useRef, useState } from 'react';
import { uploadBudget } from '../lib/api';
import type { ParsedBudget } from '../types/budget';

interface HomePageProps {
  onSelectCashflow: () => void;
  onBudgetParsed: (budget: ParsedBudget) => void;
}

export default function HomePage({ onSelectCashflow, onBudgetParsed }: HomePageProps) {
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [parsedBudget, setParsedBudget] = useState<ParsedBudget | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setUploading(true);
      setUploadError(null);
      try {
        const result = await uploadBudget(file);
        setParsedBudget(result);
        onBudgetParsed(result);
      } catch (e: any) {
        setUploadError(e.message || 'Failed to parse budget file');
      } finally {
        setUploading(false);
      }
    },
    [onBudgetParsed],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero / Banner */}
      <div className="bg-gradient-to-br from-white to-blue-50 border-b border-gray-200 h-56 overflow-hidden">
        <div className="max-w-7xl mx-auto px-6 h-full flex items-center justify-between">
          {/* Logo */}
          <img
            src="/logo.png"
            alt="Production Finance Engine"
            className="h-[432px] w-auto object-contain flex-shrink-0 -ml-[144px]"
          />

          {/* Tagline */}
          <p className="text-right text-xl text-gray-400 font-light tracking-wide leading-snug flex-shrink-0">
            comprehensive budget analysis.
            <br />
            <span className="text-blue-600 font-semibold">made simple.</span>
          </p>
        </div>
      </div>

      {/* Marketing Section */}
      <div className="bg-stone-100 py-24 px-6">
        <div className="max-w-7xl mx-auto flex flex-col lg:flex-row items-center gap-16">
          {/* Left: Copy */}
          <div className="flex-1 flex flex-col items-start">
            <h2 className="text-5xl lg:text-6xl font-bold text-slate-900 leading-[1.1] tracking-tight mb-6">
              Upload your Movie Magic budget.
            </h2>
            <p className="text-lg text-slate-600 leading-relaxed max-w-lg">
              Generate cashflow and tax credit forecasts in seconds.
            </p>
          </div>

          {/* Right: Budget Upload */}
          <div className="flex-1 w-full">
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls"
              className="hidden"
              onChange={handleInputChange}
            />

            {parsedBudget ? (
              <div
                onClick={() => fileInputRef.current?.click()}
                className="cursor-pointer bg-white rounded-2xl shadow-xl shadow-stone-300 p-10 flex flex-col items-center gap-5 border border-stone-200 hover:border-blue-300 transition-colors"
              >
                <div className="w-14 h-14 bg-green-50 rounded-full flex items-center justify-center">
                  <svg
                    className="w-7 h-7 text-green-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-500 truncate max-w-xs">
                    {parsedBudget.source_filename}
                  </p>
                  <p className="text-4xl font-bold text-slate-900 mt-3">
                    $
                    {parsedBudget.total_budget.toLocaleString('en-US', {
                      maximumFractionDigits: 0,
                    })}
                  </p>
                  <p className="text-sm text-gray-400 mt-1">total budget</p>
                </div>
                <p className="text-xs text-gray-400">
                  Click to upload a different file
                </p>
              </div>
            ) : (
              <div
                onClick={() => fileInputRef.current?.click()}
                onDrop={handleDrop}
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragOver(true);
                }}
                onDragLeave={() => setIsDragOver(false)}
                className={`w-full rounded-2xl border-2 border-dashed cursor-pointer transition-all p-16 flex flex-col items-center justify-center gap-4 shadow-xl shadow-stone-300 ${
                  isDragOver
                    ? 'border-blue-400 bg-blue-50'
                    : uploading
                      ? 'border-stone-300 bg-white'
                      : 'border-stone-300 bg-white hover:border-blue-300 hover:bg-blue-50/30'
                }`}
              >
                {uploading ? (
                  <>
                    <div className="animate-spin h-10 w-10 border-2 border-blue-500 border-t-transparent rounded-full" />
                    <p className="text-sm text-gray-500">Parsing budget...</p>
                  </>
                ) : (
                  <>
                    <svg
                      className={`w-12 h-12 ${isDragOver ? 'text-blue-400' : 'text-stone-400'}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
                      />
                    </svg>
                    <div className="text-center">
                      <p className="text-base font-medium text-slate-700">
                        {isDragOver
                          ? 'Drop your file here'
                          : 'Drop your .xlsx file here'}
                      </p>
                      <p className="text-sm text-slate-400 mt-1">
                        or click to browse
                      </p>
                    </div>
                  </>
                )}
              </div>
            )}

            {uploadError && (
              <p className="text-sm text-red-600 mt-3">{uploadError}</p>
            )}
          </div>
        </div>
      </div>

      {/* Tool Selection */}
      <main className="max-w-7xl mx-auto px-6 py-16">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-8">
          What would you like to generate?
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Cashflow Card — active */}
          <button
            onClick={onSelectCashflow}
            className="group text-left bg-white border border-gray-200 rounded-2xl p-8 shadow-sm hover:shadow-md hover:border-blue-400 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            <div className="flex items-start justify-between mb-6">
              {/* Icon */}
              <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center group-hover:bg-blue-100 transition-colors">
                <svg
                  className="w-6 h-6 text-blue-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.75}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
              </div>
              {/* Arrow */}
              <svg
                className="w-5 h-5 text-gray-300 group-hover:text-blue-500 group-hover:translate-x-0.5 transition-all"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </div>

            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Production Cashflow
            </h3>
            <p className="text-sm text-gray-500 leading-relaxed">
              Generate a week-by-week cashflow forecast from your production
              budget. Assign spend curves and phase distributions across prep,
              shoot, wrap, and post.
            </p>

            <div className="mt-6 inline-flex items-center gap-1.5 text-sm font-medium text-blue-600 group-hover:text-blue-700">
              Get started
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 7l5 5m0 0l-5 5m5-5H6"
                />
              </svg>
            </div>
          </button>

          {/* Tax Credit Filing Budget Card — coming soon */}
          <div className="relative text-left bg-white border border-gray-100 rounded-2xl p-8 shadow-sm opacity-60 cursor-not-allowed">
            {/* Coming Soon Badge */}
            <span className="absolute top-4 right-4 text-xs font-semibold text-amber-700 bg-amber-50 border border-amber-200 px-2.5 py-1 rounded-full">
              Coming soon
            </span>

            <div className="flex items-start justify-between mb-6">
              <div className="w-12 h-12 bg-gray-50 rounded-xl flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.75}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </div>
            </div>

            <h3 className="text-xl font-semibold text-gray-500 mb-2">
              Tax Credit Filing Budget
            </h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Produce a structured budget output formatted for tax credit
              applications. Automatically categorise expenditure against
              eligible spend criteria.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
