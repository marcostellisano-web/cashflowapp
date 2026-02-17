import { AlertCircle } from 'lucide-react';
import type { ParsedBudget } from '../../types/budget';
import { formatCurrency } from '../../lib/utils';

interface BudgetPreviewProps {
  budget: ParsedBudget;
  onNext: () => void;
  onReset: () => void;
}

export default function BudgetPreview({
  budget,
  onNext,
  onReset,
}: BudgetPreviewProps) {
  const noAmountWarnings = budget.warnings.filter((w) =>
    w.toLowerCase().includes('has no amount, skipped'),
  );
  const otherWarnings = budget.warnings.filter(
    (w) => !w.toLowerCase().includes('has no amount, skipped'),
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            Budget Preview
          </h2>
          <p className="text-sm text-gray-500">
            {budget.source_filename} &mdash;{' '}
            {budget.line_items.length} line items &mdash;{' '}
            Total: {formatCurrency(budget.total_budget)}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onReset}
            className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700"
          >
            Upload Different File
          </button>
          <button
            onClick={onNext}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Next: Production Parameters
          </button>
        </div>
      </div>

      {budget.warnings.length > 0 && (
        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium text-yellow-800">
            <AlertCircle className="w-4 h-4" />
            Parser Warnings ({budget.warnings.length})
          </div>

          {noAmountWarnings.length > 0 && (
            <details className="text-xs text-yellow-800 bg-yellow-100/60 rounded border border-yellow-200">
              <summary className="cursor-pointer px-2.5 py-2 font-medium">
                {noAmountWarnings.length} blank-code / no-amount line item
                {noAmountWarnings.length === 1 ? '' : 's'} skipped (show details)
              </summary>
              <ul className="px-2.5 pb-2 space-y-0.5 text-yellow-700">
                {noAmountWarnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </details>
          )}

          {otherWarnings.length > 0 && (
            <ul className="text-xs text-yellow-700 space-y-0.5">
              {otherWarnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto max-h-96">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="text-left px-4 py-2 font-medium text-gray-600">
                  Code
                </th>
                <th className="text-left px-4 py-2 font-medium text-gray-600">
                  Description
                </th>
                <th className="text-left px-4 py-2 font-medium text-gray-600">
                  Category
                </th>
                <th className="text-right px-4 py-2 font-medium text-gray-600">
                  Total
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {budget.line_items.map((item, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-4 py-1.5 font-mono text-gray-600">
                    {item.code}
                  </td>
                  <td className="px-4 py-1.5 text-gray-900">
                    {item.description}
                  </td>
                  <td className="px-4 py-1.5">
                    <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                      {item.category?.replace(/_/g, ' ') || 'other'}
                    </span>
                  </td>
                  <td className="px-4 py-1.5 text-right font-mono">
                    {formatCurrency(item.total)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
