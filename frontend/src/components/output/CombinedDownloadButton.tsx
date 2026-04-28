import { useState } from 'react';
import { Download } from 'lucide-react';
import type { ParsedBudget } from '../../types/budget';
import type { LineItemDistribution } from '../../types/cashflow';
import type { ProductionParameters } from '../../types/production';
import { generateCombinedExcel } from '../../lib/api';
import { downloadBlob } from '../../lib/utils';

interface CombinedDownloadButtonProps {
  budget: ParsedBudget;
  parameters: ProductionParameters;
  distributions: LineItemDistribution[];
}

export default function CombinedDownloadButton({
  budget,
  parameters,
  distributions,
}: CombinedDownloadButtonProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDownload = async () => {
    setLoading(true);
    setError(null);
    try {
      const blob = await generateCombinedExcel(budget, parameters, distributions);
      const filename = `${parameters.title.replace(/\s+/g, '_')}_combined.xlsx`;
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
        className="flex items-center gap-2 px-6 py-3 bg-violet-600 text-white rounded-lg hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
      >
        {loading ? (
          <>
            <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
            Generating...
          </>
        ) : (
          <>
            <Download className="w-5 h-5" />
            Download Combined Report
          </>
        )}
      </button>
      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}
