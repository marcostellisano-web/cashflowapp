import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileSpreadsheet, AlertCircle } from 'lucide-react';
import type { ParsedBudget } from '../../types/budget';
import { uploadBudget } from '../../lib/api';

interface BudgetUploaderProps {
  onParsed: (budget: ParsedBudget) => void;
}

export default function BudgetUploader({ onParsed }: BudgetUploaderProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;

      setLoading(true);
      setError(null);

      try {
        const parsed = await uploadBudget(file);
        onParsed(parsed);
      } catch (e: any) {
        setError(e.message || 'Failed to parse budget file');
      } finally {
        setLoading(false);
      }
    },
    [onParsed],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    maxFiles: 1,
  });

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">
          Upload Budget File
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          Upload a Movie Magic Budgeting export (.xlsx) with budget codes,
          descriptions, and totals.
        </p>
      </div>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400 bg-white'
        }`}
      >
        <input {...getInputProps()} />
        {loading ? (
          <div className="flex flex-col items-center gap-2">
            <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full" />
            <p className="text-sm text-gray-500">Parsing budget file...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            {isDragActive ? (
              <FileSpreadsheet className="w-12 h-12 text-blue-500" />
            ) : (
              <Upload className="w-12 h-12 text-gray-400" />
            )}
            <div>
              <p className="text-sm font-medium text-gray-700">
                {isDragActive
                  ? 'Drop the file here'
                  : 'Drag & drop your budget Excel file here'}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                or click to browse (.xlsx, .xls)
              </p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}
    </div>
  );
}
