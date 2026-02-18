import { useMemo } from 'react';
import { FileSpreadsheet, FileDown } from 'lucide-react';
import type { ParsedBudget } from '../../types/budget';
import type { CashflowOutput, LineItemDistribution } from '../../types/cashflow';
import type { ProductionParameters } from '../../types/production';
import DownloadButton from './DownloadButton';
import { downloadTextFile } from '../../lib/utils';

interface ExportCenterProps {
  budget: ParsedBudget | null;
  parameters: ProductionParameters | null;
  distributions: LineItemDistribution[];
  preview: CashflowOutput | null;
}

function toCurrencyString(value: number): string {
  return Number.isFinite(value) ? value.toFixed(2) : '0.00';
}

function sanitizeTitle(value: string): string {
  return value.trim().replace(/\s+/g, '_').replace(/[^\w-]/g, '') || 'export';
}

export default function ExportCenter({
  budget,
  parameters,
  distributions,
  preview,
}: ExportCenterProps) {
  const budgetCsv = useMemo(() => {
    if (!budget) return null;

    const header = ['Code', 'Description', 'Category', 'Account Group', 'Total'];
    const rows = budget.line_items.map((item) => [
      item.code,
      item.description,
      item.category ?? '',
      item.account_group ?? '',
      toCurrencyString(item.total),
    ]);

    const allRows = [header, ...rows];
    return allRows
      .map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(','))
      .join('\n');
  }, [budget]);

  const cashflowCsv = useMemo(() => {
    if (!preview) return null;

    const weekHeaders = preview.weeks.map((w) => `Week ${w.week_number} (${w.week_commencing})`);
    const header = ['Code', 'Description', 'Total', ...weekHeaders];

    const rows = preview.rows.map((row) => [
      row.code,
      row.description,
      toCurrencyString(row.total),
      ...row.weekly_amounts.map(toCurrencyString),
    ]);

    rows.push([
      'TOTAL',
      'Weekly Totals',
      toCurrencyString(preview.grand_total),
      ...preview.weekly_totals.map(toCurrencyString),
    ]);

    return [header, ...rows]
      .map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(','))
      .join('\n');
  }, [preview]);

  const filePrefix = sanitizeTitle(parameters?.title || budget?.source_filename || 'production_finance');

  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm space-y-4">
      <div>
        <h3 className="text-base font-semibold text-gray-900">Export Center</h3>
        <p className="text-sm text-gray-500">
          Export your current budget and generated cashflow in spreadsheet-friendly formats.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        <button
          onClick={() => budgetCsv && downloadTextFile(budgetCsv, `${filePrefix}_budget.csv`, 'text/csv')}
          disabled={!budgetCsv}
          className="flex items-center justify-center gap-2 rounded-xl border border-gray-300 px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <FileSpreadsheet className="h-4 w-4" />
          Export Budget (CSV)
        </button>

        <button
          onClick={() => cashflowCsv && downloadTextFile(cashflowCsv, `${filePrefix}_cashflow.csv`, 'text/csv')}
          disabled={!cashflowCsv}
          className="flex items-center justify-center gap-2 rounded-xl border border-gray-300 px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <FileDown className="h-4 w-4" />
          Export Cashflow (CSV)
        </button>

        {budget && parameters && distributions.length > 0 && (
          <div className="sm:col-span-2 xl:col-span-1">
            <DownloadButton
              budget={budget}
              parameters={parameters}
              distributions={distributions}
              label="Export Cashflow (Excel)"
            />
          </div>
        )}
      </div>
    </section>
  );
}
