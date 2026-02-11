import type { CashflowOutput } from '../../types/cashflow';
import { formatCurrency } from '../../lib/utils';

interface CashflowPreviewProps {
  output: CashflowOutput;
}

export default function CashflowPreview({ output }: CashflowPreviewProps) {
  // Find the max weekly total for heatmap intensity
  const maxWeekly = Math.max(...output.weekly_totals, 1);

  return (
    <div className="space-y-4">
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="font-medium text-gray-900 mb-2">Weekly Spend Overview</h3>
        <div className="flex gap-1 items-end h-32">
          {output.weekly_totals.map((total, i) => {
            const height = (total / maxWeekly) * 100;
            const week = output.weeks[i];
            return (
              <div
                key={i}
                className="flex-1 min-w-1 group relative"
                title={`Wk ${week.week_number}: ${formatCurrency(total)} - ${week.phase_label}`}
              >
                <div
                  className="bg-blue-500 rounded-t-sm w-full transition-all hover:bg-blue-600"
                  style={{ height: `${Math.max(height, 1)}%` }}
                />
              </div>
            );
          })}
        </div>
        <div className="flex justify-between mt-2 text-xs text-gray-400">
          <span>Wk 1</span>
          <span>Wk {output.weeks.length}</span>
        </div>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-500">Grand Total</div>
          <div className="text-2xl font-bold text-gray-900">
            {formatCurrency(output.grand_total)}
          </div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-500">Budget Lines</div>
          <div className="text-2xl font-bold text-gray-900">
            {output.rows.length}
          </div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-500">Weeks</div>
          <div className="text-2xl font-bold text-gray-900">
            {output.weeks.length}
          </div>
        </div>
      </div>

      {/* Data table preview */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto max-h-80">
          <table className="text-xs w-full">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="text-left px-2 py-1.5 font-medium text-gray-600 sticky left-0 bg-gray-50 z-10">
                  Description
                </th>
                <th className="text-right px-2 py-1.5 font-medium text-gray-600">
                  Total
                </th>
                {output.weeks.map((w) => (
                  <th
                    key={w.week_number}
                    className="text-right px-1 py-1.5 font-medium text-gray-400 min-w-16"
                  >
                    Wk {w.week_number}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {output.rows.map((row, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-2 py-1 text-gray-900 truncate max-w-40 sticky left-0 bg-white z-10">
                    {row.description}
                  </td>
                  <td className="px-2 py-1 text-right font-mono text-gray-700">
                    {formatCurrency(row.total)}
                  </td>
                  {row.weekly_amounts.map((amount, wi) => (
                    <td
                      key={wi}
                      className="px-1 py-1 text-right font-mono"
                      style={{
                        backgroundColor:
                          amount > 0
                            ? `rgba(59, 130, 246, ${Math.min(amount / (row.total * 0.2), 0.3)})`
                            : undefined,
                      }}
                    >
                      {amount > 0 ? formatCurrency(amount) : ''}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-blue-50 sticky bottom-0">
              <tr className="font-bold">
                <td className="px-2 py-1.5 sticky left-0 bg-blue-50 z-10">
                  WEEKLY TOTAL
                </td>
                <td className="px-2 py-1.5 text-right font-mono">
                  {formatCurrency(output.grand_total)}
                </td>
                {output.weekly_totals.map((total, i) => (
                  <td key={i} className="px-1 py-1.5 text-right font-mono">
                    {total > 0 ? formatCurrency(total) : ''}
                  </td>
                ))}
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  );
}
