import { useState } from 'react';
import { Download } from 'lucide-react';
import type { ParsedBudget } from '../../types/budget';
import type { LineItemDistribution } from '../../types/cashflow';
import type { ProductionParameters } from '../../types/production';
import { generateCashflowExcel } from '../../lib/api';
import { downloadBlob } from '../../lib/utils';

interface DownloadButtonProps {
  budget: ParsedBudget;
  parameters: ProductionParameters;
  distributions: LineItemDistribution[];
  label?: string;
}

export default function DownloadButton({
  budget,
  parameters,
  distributions,
  label = 'Download Excel',
}: DownloadButtonProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDownload = async () => {
    setLoading(true);
    setError(null);
    try {
      const blob = await generateCashflowExcel(
        budget,
        parameters,
        distributions,
      );
      const filename = `${parameters.title.replace(/\s+/g, '_')}_cashflow.xlsx`;
      downloadBlob(blob, filename);
    } catch (e: any) {
      setError(e.message || 'Download failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-2">
      <button
        onClick={handleDownload}
        disabled={loading}
        className="flex w-full items-center justify-center gap-2 rounded-xl bg-green-600 px-5 py-3 text-sm font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? (
          <>
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            Generating...
          </>
        ) : (
          <>
            <Download className="h-5 w-5" />
            {label}
          </>
        )}
      </button>
      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}
