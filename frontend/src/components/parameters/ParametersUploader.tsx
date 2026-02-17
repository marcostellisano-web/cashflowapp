import { useState, useRef } from 'react';
import type { ProductionParameters } from '../../types/production';
import { uploadParameters, getParametersTemplateUrl } from '../../lib/api';

interface ParametersUploaderProps {
  onParsed: (params: ProductionParameters) => void;
  onManual: () => void;
  onBack: () => void;
}

export default function ParametersUploader({ onParsed, onManual, onBack }: ParametersUploaderProps) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      setError('Please upload an Excel file (.xlsx)');
      return;
    }
    setUploading(true);
    setError(null);
    try {
      const params = await uploadParameters(file);
      onParsed(params);
    } catch (e: any) {
      setError(e.message || 'Failed to parse parameters file');
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Production Parameters</h2>
          <p className="text-sm text-gray-500">Choose how to enter your production schedule.</p>
        </div>
        <button
          type="button"
          onClick={onBack}
          className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700"
        >
          Back
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Option 1: Enter Manually */}
        <button
          type="button"
          onClick={onManual}
          className="bg-white border-2 border-gray-200 rounded-lg p-6 text-left hover:border-blue-400 hover:bg-blue-50/30 transition-colors group"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center text-blue-600 group-hover:bg-blue-200">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </div>
            <h3 className="font-medium text-gray-900">Enter Manually</h3>
          </div>
          <p className="text-sm text-gray-500">
            Fill in production dates, shooting blocks, and delivery milestones using the form interface.
          </p>
        </button>

        {/* Option 2: Upload Excel */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInput.current?.click()}
          className={`bg-white border-2 rounded-lg p-6 text-left cursor-pointer transition-colors ${
            dragOver
              ? 'border-blue-400 bg-blue-50/30'
              : 'border-gray-200 hover:border-blue-400 hover:bg-blue-50/30'
          } ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
        >
          <input
            ref={fileInput}
            type="file"
            accept=".xlsx,.xls"
            onChange={handleInputChange}
            className="hidden"
          />
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center text-green-600">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <h3 className="font-medium text-gray-900">
              {uploading ? 'Parsing...' : 'Upload Excel'}
            </h3>
          </div>
          <p className="text-sm text-gray-500">
            Upload a parameters spreadsheet with Info, Shooting Blocks, and Episode Deliveries sheets.
          </p>
          {uploading && (
            <div className="mt-3 flex items-center gap-2">
              <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full" />
              <span className="text-xs text-gray-500">Parsing file...</span>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="text-center">
        <a
          href={getParametersTemplateUrl()}
          className="text-sm text-blue-600 hover:text-blue-700 underline"
          download
        >
          Download blank Excel template
        </a>
      </div>
    </div>
  );
}
