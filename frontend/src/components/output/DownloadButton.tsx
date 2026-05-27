import { useState } from 'react';
import { Download } from 'lucide-react';
import type { ParsedBudget } from '../../types/budget';
import type { LineItemDistribution } from '../../types/cashflow';
import type { ProductionParameters } from '../../types/production';
import { generateCashflowExcel, generateFormulaCashflowExcel } from '../../lib/api';
import { downloadBlob } from '../../lib/utils';

interface DownloadButtonProps {
  budget: ParsedBudget;
  parameters: ProductionParameters;
  distributions: LineItemDistribution[];
}

export default function DownloadButton({
  budget,
  parameters,
  distributions,
}: DownloadButtonProps) {
  const [loadingValues, setLoadingValues] = useState(false);
  const [loadingFormulas, setLoadingFormulas] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDownload = async (mode: 'values' | 'formulas') => {
    const setLoading = mode === 'values' ? setLoadingValues : setLoadingFormulas;
    setLoading(true);
    setError(null);
    try {
      const blob =
        mode === 'values'
          ? await generateCashflowExcel(budget, parameters, distributions)
          : await generateFormulaCashflowExcel(budget, parameters, distributions);
      const suffix = mode === 'formulas' ? '_formulas' : '';
      const filename = `${parameters.title.replace(/\s+/g, '_')}_cashflow${suffix}.xlsx`;
      downloadBlob(blob, filename);
    } catch (e: any) {
      setError(e.message || 'Download failed');
    } finally {
      setLoading(false);
    }
  };

  const loading = loadingValues || loadingFormulas;

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        <button
          onClick={() => handleDownload('values')}
          disabled={loading}
          className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
        >
          {loadingValues ? (
            <>
              <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
              Generating...
            </>
          ) : (
            <>
              <Download className="w-5 h-5" />
              Download Excel
            </>
          )}
        </button>

        <button
          onClick={() => handleDownload('formulas')}
          disabled={loading}
          className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
        >
          {loadingFormulas ? (
            <>
              <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
              Generating...
            </>
          ) : (
            <>
              <Download className="w-5 h-5" />
              Download Excel (Formulas)
            </>
          )}
        </button>
      </div>
      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}
